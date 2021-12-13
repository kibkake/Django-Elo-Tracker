from django.http.response import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import GameRegisterForm,AddResultsForm,CreateCompanyForm, companyInviteForm
from .models import Company, Game,Match
from django.utils.timezone import get_default_timezone_name
from .forms import GameRegisterForm,AddResultsForm,CreateCompanyForm, AddUpcomingForm,PromoteAdminForm
from .models import Company, Game, Match, Upcoming, EloRating
from users.models import User, Profile
from django.views.generic.detail import DetailView
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.decorators import login_required
from datetime import date
from django.utils.crypto import get_random_string
from django.urls import reverse_lazy
from django.core.mail import send_mail
from django.conf import settings
from stats.filters import UpcomingFilter
from trueskill import Rating, rate_1vs1, expose, setup

def home(request):
    return redirect('stats-home-refresh', slug='default')

def homeRefresh(request, slug):
    if (request.user.is_authenticated):
        if(not request.user.profile.company):
            return redirect('stats-company')
        context = {}
        user_profile = Profile.objects.filter(user = request.user).first()
        Games = Game.objects.filter(company = user_profile.company)
        if (not Games.exists()):
            return render(request, 'stats/home.html')
        context['Games'] = Games
        Leaders = []
        Recent_Matches = []
        Upcoming_Matches = []
        game = []
        if (slug == 'default'):
            game = Games.first()
        else:
            if (Games.filter(slug = slug).exists()):
                game = Games.filter(company=user_profile.company, slug = slug).first()
        if (isinstance(game,Game)):
            top_ratings = list(EloRating.objects.filter(game = game.id).order_by('-mu')[:3].values_list('player', flat=True))
            for player in top_ratings:
                Leaders.append(User.objects.get(id=player))
            Recent_Matches = Match.objects.filter(game = game.id, match_date__lt=date.today()).order_by('match_date')[:5]
            Recent_Players = []
            for match in Recent_Matches:
                Recent_Players.append([match.player_A.username,match.player_B.username])
            Upcoming_Matches = Match.objects.filter(game = game.id, match_date__gte=date.today()).order_by('match_date')[:5]
            context['Leaders'] = Leaders
            context['Histories'] = Recent_Matches
            context['Upcomings'] = Upcoming_Matches
            context['game_title'] = game.title
        return render(request, 'stats/home.html', context)
    else:
        return render(request, 'stats/home.html')

def about(request):
    return render(request, 'stats/about.html')

def newgame(request):
    if request.method == 'POST':
        form = GameRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f'Your game has been created!')
            return redirect('stats-home')
    else:
        if( request.user.is_authenticated):
            if(not request.user.profile.company):
                return redirect('stats-company')
        form = GameRegisterForm()
    return render(request, 'stats/newgame.html', {'form': form})

class GameDetailView(DetailView,LoginRequiredMixin):
    context_object_name = 'game_detail'
    template_name = 'stats/game.html' 
    model = Game
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super(GameDetailView, self).get_context_data(**kwargs)
        context['Matches'] = Match.objects.filter(game=self.get_object())
        if EloRating.objects.filter(player=self.request.user.id, game=self.get_object()).exists():
            context['EloRating'] = EloRating.objects.get(player=self.request.user.id, game=self.get_object())
        else:
            context['EloRating'] = None
        return context

def results(request, **kwargs):
    slug = kwargs['slug']
    game = Game.objects.get(slug=slug)

    if request.method == 'POST':
        form = AddResultsForm(request.POST)

        if form.is_valid():
            player_A = EloRating.objects.get(player = form.cleaned_data['player_A'], game = game)
            player_B = EloRating.objects.get(player = form.cleaned_data['player_B'], game = game)

            form.instance.game = game
            form.instance.elo_A = expose(Rating(mu=player_A.mu, sigma=player_A.sigma))
            form.instance.elo_B = expose(Rating(mu=player_B.mu, sigma=player_B.sigma))

            if form.cleaned_data['score_A'] == form.cleaned_data['score_B']:
                newElo_A, newElo_B = rate_1vs1(Rating(mu=player_A.mu, sigma=player_A.sigma), Rating(mu=player_B.mu, sigma=player_B.sigma), drawn=True)
                
            elif form.cleaned_data['score_A'] > form.cleaned_data['score_B']:
                newElo_A, newElo_B = rate_1vs1(Rating(mu=player_A.mu, sigma=player_A.sigma), Rating(mu=player_B.mu, sigma=player_B.sigma))
            else:
                newElo_B, newElo_A = rate_1vs1(Rating(mu=player_B.mu, sigma=player_B.sigma), Rating(mu=player_A.mu, sigma=player_A.sigma))
            
            player_A.mu, player_A.sigma = newElo_A
            player_B.mu, player_B.sigma = newElo_B
            player_A.save()
            player_B.save()

            form.save()
            messages.success(request, f'Your match results were added!')
            return redirect('stats-home')
    else:
        form = AddResultsForm()
    return render(request, 'stats/results.html',{'form': form})

class ResultsDetailView(DetailView, LoginRequiredMixin):
    context_object_name = 'results_detail'
    template_name = 'stats/results.html' 
    model = Match
    slug_url_kwarg = 'slug'

@login_required
def company(request):
    if request.method == 'POST':
        if 'promoteUser' in request.POST:
            form = PromoteAdminForm(request.user.profile.company,request.POST)
            if form.is_valid():
                user=form.cleaned_data.get('chosenUser')
                request.user.profile.company.admins.add(user.user)
            return HttpResponseRedirect(request.path_info)
        else:
            form = companyInviteForm(request.POST)
            if form.is_valid():
                inviteCode=form.cleaned_data.get('inviteCode')
                companyQuery = Company.objects.filter(invite_code=inviteCode)
                if companyQuery:
                    request.user.profile.company=companyQuery.get()
                    request.user.profile.save()
                    messages.info(request,f'Successully registered with company '+ companyQuery.get().name)
                    return HttpResponseRedirect(request.path_info)
                else: 
                    messages.error(request,f'Invite code not valid')
            return render(request, 'stats/company.html',{'form':form})
    else:
        company = request.user.profile.company
        admins=[]
        if company:
            admins=company.admins.all()
        isAdmin = request.user in admins
        users = Profile.objects.all().filter(company=company)
        form = companyInviteForm()
        adminForm=None
        if(isAdmin):
            adminForm = PromoteAdminForm(company=company)
        return render(request, 'stats/company.html',{'company': company,'admins':admins,'users':users,'form':form,'adminForm':adminForm,'isAdmin':isAdmin})

def createCompany(request):
    if request.method == 'POST':
        form = CreateCompanyForm(request.POST)
        if form.is_valid():
            company = form.save()
            company.invite_code = get_random_string(length=32)
            company.save()
            company.admins.add(request.user)
            request.user.profile.company=company
            request.user.save()
            messages.success(request, f'Your company has been created!')
            return redirect('stats-home')
    else:
        form = CreateCompanyForm()
    return render(request, 'stats/createCompany.html', {'form': form})

def schedule(request):
    if( request.user.is_authenticated):
        if(not request.user.profile.company):
            return redirect('stats-company')
    return render(request, 'stats/schedule.html')

def newmatch(request):
    if request.method == 'POST':
        form = AddUpcomingForm(request.POST)
        if form.is_valid():
            upcoming = form.cleaned_data
            subject = "Upcoming Match"
            message = "Hello, here is a friendly reminder you have an upcoming match scheduled!"
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [upcoming['player_1'].email, upcoming['player_2'].email])
            form.save()
            messages.success(request, f'A match has been scheduled & participants will be notified through email!')

            return redirect('stats-schedule')
    else:
        form = AddUpcomingForm()
    return render(request, 'stats/newmatch.html', {'form': form})

class UpcomingList(ListView,LoginRequiredMixin):
    model = Upcoming
    template_name = 'stats/schedule.html'
    context_object_name = 'upcomings'
    ordering = ['date','start_time']

class UpcomingDetailView(DetailView,LoginRequiredMixin):
    model = Upcoming
    template_name = 'stats/upcoming.html'

def joinGame(request, **kwargs):
    setup(mu=1000, sigma=333.333, tau=3.33333, beta=166.666)  
    slug = kwargs['slug']
    game = Game.objects.filter(slug=slug)[0]

    if EloRating.objects.filter(player=request.user.id, game=game).exists():
        print('jh')
    else:
        rating = EloRating()
        rating.player = request.user
        rating.game = game
        rating.mu, rating.sigma = Rating(1000)
        rating.save()

    return redirect('stats-home')
class UpcomingUpdateView(SuccessMessageMixin, UpdateView):
    model = Upcoming
    template_name = 'stats/updatematch.html'
    form_class = AddUpcomingForm
    success_message = 'Upcoming match successfully updated!'

class UpcomingDeleteView(DeleteView):
    model = Upcoming
    template_name = 'stats/deletematch.html'
    success_url = reverse_lazy('stats-schedule')

def search(request):
    if( request.user.is_authenticated):
        if(not request.user.profile.company):
            return redirect('stats-company')

    upcoming_list = Upcoming.objects.all()
    upcoming_filter = UpcomingFilter(request.GET, queryset=upcoming_list)
    return render(request, 'stats/schedule.html', {'filter': upcoming_filter})
    
