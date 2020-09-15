from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from  django.contrib.auth.models import User
from django.urls import reverse
from rango.models import Category, Page, UserProfile
from rango.forms import CategoryForm, PageForm
from rango.forms import UserForm, UserProfileForm
from django.contrib.auth.decorators import login_required
from datetime import datetime
from rango.webhose_search import run_query
from django.shortcuts import redirect


def index(request):
    request.session.set_test_cookie()
    # Запросить в базе данных список ВСЕХ категорий, хранящихся в данный момент.
    # Упорядочить категории по количеству лайков в порядке убывания.
    # Получить только первые 5 - или все, если меньше 5.
    # Поместите список в наш словарь context_dict, который будет передан шаблонизатору.
    category_list = Category.objects.order_by('-likes')[:5]
    page_list = Page.objects.order_by('-views')[:5]
    context_dict = {'categories': category_list, 'pages': page_list}

    # Вызвать вспомогательную функцию для обработки файлов cookie
    visitor_cookie_handler(request)
    context_dict['visits'] = request.session['visits']


    # Получите наш объект Response заранее, чтобы мы могли добавить информацию о cookie.
    response = render(request, 'rango/index.html', context=context_dict)

    # Вернуть ответ пользователю, обновив все файлы cookie, которые необходимо изменить.
    return response


def about(request):
    visitor_cookie_handler(request)
    print('Это из индекса', request.session['visits'])
    last_date = request.session['last_visit'][:-7]  # удаляю дробную часть секунд из даты
    context_dict = {'aboutmessage': 'Here you can say everything you want about Rango',
                    'number_of_visits': request.session['visits'],
                    'date_of_last_visit': last_date}
    return render(request, 'rango/about.html', context=context_dict)

def show_category(request, category_name_slug):
    # Создайте контекстный словарь, который мы можем передать
    # в механизм визуализации шаблонов.
    context_dict = {}

    try:
        # Можем ли мы найти слаг с именем категории с заданным именем?
        # Если мы не можем, метод .get () вызывает исключение DoesNotExist.
        # Таким образом, метод .get () возвращает один экземпляр модели или вызывает исключение
        category = Category.objects.get(slug=category_name_slug)

        # Получить все связанные страницы.
        # Обратите внимание, что filter () вернет список объектов страницы
        # или пустой список.
        pages = Page.objects.filter(category=category)

        # Добавляет наш список результатов в контекст шаблона под именными страницами
        context_dict['pages'] = pages
        # Мы также добавляем объект категории из базы данных в контекстный словарь.
        # Мы будем использовать это в шаблоне, чтобы убедиться,
        # что категория существует
        context_dict['category'] = category
    except Category.DoesNotExist:
        # Мы попадаем сюда, если не нашли указанную категорию.
        # Не делай ничего
        # шаблон покажет нам сообщение «нет категории».
        context_dict['category'] = None
        context_dict['pages'] = None

    # Перейти к ответу и вернуть его клиенту
    return render(request, 'rango/category.html', context_dict)

def add_category(request):
    form = CategoryForm()

    # A HTTP POST?
    if request.method == 'POST':
        form = CategoryForm(request.POST)

        # Нам предоставили действительную форму?
        if form.is_valid():
            # Сохранить новую категорию в базе данных.
            form.save(commit=True)
            # Теперь, когда категория сохранена,
            # мы можем выдать подтверждающее сообщение,
            # но поскольку последняя добавленная категория
            # находится на странице индекса, то мы можем
            # направить пользователя обратно на страницу индекса.
            return index(request)
        else:
            # В предоставленной форме есть ошибки -
            # просто распечатайте их в терминал
            print(form.errors)
    # Будет обрабатывать плохую форму, новую форму или не предоставленные формы.
    # Рендеринг формы с сообщениями об ошибках (если есть).
    return render(request, 'rango/add_category.html', {'form': form})

def add_page(request, category_name_slug):
    try:
        category = Category.objects.get(slug=category_name_slug)
    except Category.DoesNotExist:
        category = None

    form = PageForm()
    if request.method =='POST':
        form = PageForm(request.POST)
        if form.is_valid():
            if category:
                page = form.save(commit=False)
                page.category = category
                page.views = 0
                page.save()
                # переход на страницу category.html после отправки данных через форму
                return show_category(request, category_name_slug)
        else:
            print(form.errors)
    # если данные через форму не отправляли, открывется страница add_page.html
    context_dict = {'form': form, 'category': category}
    return render(request, 'rango/add_page.html', context_dict)


def register(request):
    # Булево значение для описания шаблона
    # была ли регистрация успешной.
    # Сначала установите False. Код меняет значение на
    # True, когда регистрация прошла успешно
    registered = False

    # Если это HTTP POST, мы заинтересованы в обработке данных формы.
    if request.method == 'POST':
        # Попытка получить информацию из необработанной информации формы.
        # Обратите внимание, что мы используем как UserForm, так и UserProfileForm.
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST)

        # Если две формы действительны ...
        if user_form.is_valid() and profile_form.is_valid():
            # Сохранить данные формы пользователя в базу данных.
            user = user_form.save()

            # Теперь мы хэшируем пароль с помощью метода set_password.
            # После хеширования мы можем обновить объект user.
            user.set_password(user.password)
            user.save()

            # Теперь рассортируйте экземпляр UserProfile.
            # Так как нам нужно самим установить атрибут пользователя,
            # мы устанавливаем commit = False. Это задерживает сохранение
            # модели до тех пор, пока мы не будем готовы избежать проблем с целостностью.
            profile = profile_form.save(commit=False)
            profile.user = user

            # Пользователь предоставил фотографию профиля?
            # Если это так, нам нужно получить его из формы ввода и
            # поместить в модель UserProfile.
            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']

            # Теперь мы сохраняем экземпляр модели UserProfile.
            profile.save()

            # Обновите нашу переменную, чтобы указать,
            # что регистрация шаблона прошла успешно.
            registered = True
        else:
            # Неправильная форма или формы - ошибки или что-то еще?
            # Проблемы с печатью в терминале.
            print(user_form.errors, profile_form.errors)
    else:
        # Не HTTP POST, поэтому мы визуализируем нашу форму,
        # используя два экземпляра ModelForm.
        # Эти формы будут пустыми, готовыми для ввода пользователем.
        user_form = UserForm()
        profile_form = UserProfileForm()

    # Визуализировать шаблон в зависимости от контекста.
    return render(request,
                  'rango/register.html',
                  {'user_form': user_form,
                   'profile_form': profile_form,
                   'registered': registered})


def user_login(request):
    # Если запрос HTTP POST, попробуйте вытащить соответствующую информацию
    if request.method == 'POST':
        # Соберите имя пользователя и пароль, предоставленные пользователем.
        # Эта информация получена из формы авторизации.
        # Мы используем request.POST.get ('<variable>')
        # в отличие от request.POST ['<variable>'],
        # потому что request.POST.get ('<variable>')
        # возвращает None, если значение не существует,
        # а request.POST ['<variable>'] вызовет исключение KeyError.
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Используйте механизм Django,
        # чтобы попытаться проверить, является ли комбинация
        # имя пользователя / пароль действительной - объект User возвращается, если он есть.
        user = authenticate(username=username, password=password)

        # Если у нас есть объект User, детали верны.
        # Если None (способ представления отсутствия в Python),
        # пользователь с соответствующими учетными данными не найден.
        if user:
            # Активен ли аккаунт? Он мог быть отключен.
            if user.is_active:
                # Если учетная запись действительна и активна,
                # мы можем войти в систему пользователя.
                # Мы отправим пользователя обратно на домашнюю страницу.
                login(request, user)
                return HttpResponseRedirect(reverse('index'))
            else:
                # Использован неактивный аккаунт - не входить!
                return HttpResponse('Your Rango account is disabled.')
        else:
            # Указаны неверные данные для входа.
            # Поэтому мы не можем войти в систему.
            print('Invalid login details: {0}, {1}'.format(username, password))
            return HttpResponse('Invalid login details supplied.')

    # Запрос не является HTTP POST, поэтому отобразите форму входа.
    # Этот сценарий, скорее всего, будет HTTP GET.
    else:
        # Нет переменных контекста для передачи в систему шаблонов,
        # следовательно, пустой объект словаря ...
        return render(request, 'rango/login.html', {})


@login_required
def restricted(request):
    # return HttpResponse("Since you're logged in, you can see this text!")
    context_dict = {'restricted_text': 'Это страница с ограниченным доступом'}
    return render(request, 'rango/restricted.html', context_dict)

# Используйте декоратор login_required (), чтобы обеспечить доступ
# к представлению только зарегистрированным пользователям.
@login_required
def user_logout(request):
    # Так как мы знаем, что пользователь вошел в систему,
    # теперь мы можем просто вывести его из неё.
    logout(request)
    # Вернуть пользователя на домашнюю страницу.
    return HttpResponseRedirect(reverse('index'))

@login_required
def register_profile(request):
    form = UserProfileForm()

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES)
        if form.is_valid():
            user_profile = form.save(commit=False)
            user_profile.user = request.user
            user_profile.save()

            return redirect('index')
        else:
            print(form.errors)
    context_dict = {'form':form}

    return render(request, 'rango/profile_registration.html', context_dict)


def get_server_side_cookie(request, cookie, default_val=None):
    val = request.session.get(cookie)
    if not val:
        val = default_val
    return val

def visitor_cookie_handler(request):
    visits = int(get_server_side_cookie(request, 'visits', '1'))

    last_visit_cookie = get_server_side_cookie(request, 'last_visit', str(datetime.now()))
    last_visit_time = datetime.strptime(last_visit_cookie[:-7], '%Y-%m-%d %H:%M:%S')

    # Если с момента последнего посещения прошло больше секунды ...
    if (datetime.now() - last_visit_time).seconds > 0:
        visits = visits +1
        # Обновите файл cookie последнего посещения теперь, когда мы обновили счетчик
        request.session['last_visit'] = str(datetime.now())
    else:
        # Установить файл cookie последнего посещения
        request.session['last_visit'] = last_visit_cookie

    # Обновить / установить cookie посещений
    request.session['visits'] = visits

def test_cookie(request):
    if not request.COOKIES.get('team'):
        response = HttpResponse("Visiting for the first time.")
        response.set_cookie('team', 'barcelona')
        return response
    else:
        return HttpResponse("Your favorite team is {}".format(request.COOKIES['team']))

def search(request):
    result_list = []
    request_text = ''

    if request.method == 'POST':
        query = request.POST['query'].strip()
        if query:
            # Запустите нашу функцию поиска Webhose, чтобы получить список результатов!
            result_list = run_query(query)
            request_text = query        # если был запрос, возвращаю его в поле запроса
    return render(request, 'rango/search.html', {'result_list': result_list,
                                                 'request_text': request_text})

def track_url(request):
    page_id = None
    url = '/rango'
    if request.method == 'GET':
        if 'page_id' in request.GET:
            page_id = request.GET['page_id']

            try:
                page = Page.objects.get(page_id=page_id)
                page.views  = page.views + 1
                page.save()
                url = page.url

            except:
                pass
    return redirect(url)

@login_required
def profile(request, username):
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return redirect('index')

    userprofile = UserProfile.objects.get_or_create(user=user)[0]
    form = UserProfileForm({'website': userprofile.website, 'picture': userprofile.picture})

    if request.method =='POST':
        form = UserProfileForm(request.POST, request.FILES, instance=userprofile)
        if form.is_valid():
            form.save(commit=True)
            return redirect('rango:profile', user.username)
        else:
            print(form.errors)

    return render(request, 'rango/profile.html', {'userprofile': userprofile, 'selecteduser': user, 'form': form})

@login_required
def list_profiles(request):
    userprofile_list = UserProfile.objects.all()

    return render(request, 'rango/list_profiles.html', {'userprofile_list': userprofile_list})

@login_required
def like_category(request):
    cat_id = None
    if request.method == 'GET':
        cat_id = request.GET['category_id']
        likes = 0
        if cat_id:
            cat = Category.objects.get(id=int(cat_id))
            if cat:
                likes = cat.likes + 1
                cat.likes = likes
                cat.save()
    return HttpResponse (likes)







