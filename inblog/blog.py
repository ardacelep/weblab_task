from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps
from datetime import datetime
import locale
locale.setlocale(locale.LC_ALL,"")


### BU BLOG'UN AYNI KULLANICI İSMİYLE BİRDEN FAZLA KEZ KAYDOLABİLME GİBİ ÇOK BÜYÜK BİR EKSİĞİ VAR.
### USERNAME PRIMARY KEY DEĞİL, DÜZELTİLMEDEN KULLANILMAMALI !!!
### REGISTER KISMINDAKİ BİR DEĞİŞİKLİKLE PATCH'LENDİ, ŞU AN DÜZGÜN ÇALIŞIYOR ANCAK EN BAŞTA DATABASE
### MİMARİSİ BENCE HALA YANLIŞ.


# kullanıcı girişi kontrolü decorator'ı
## https://flask.palletsprojects.com/en/3.0.x/patterns/viewdecorators/ adresinden kopyalandı.
def login_required(f): # yalnızca oturum açıkken kullanılabilecek sayfalarda oturum kontrolü için decorator.
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session: # session'a "logged_in" bilgisi girmişsek;
            return f(*args,**kwargs) # fonskiyonu çalıştırır.
        else: # girmemişsek.
            flash("Bu sayfayı kullanmak için lütfen giriş yapın!",category="danger") # bu flash'ı patlatır
            return redirect(url_for("login")) # ve giriş sayfasına yönlendirir.
    return decorated_function

# kullanıcı kayıt formu
class RegisterForm(Form): # Form sınıfından miras alarak kendi kayıt formu alt sınıfımızı açtık.

    # burada form alanlarımızı belirledik.
    # StringField() <input type="text"> gibi bir form alanı oluşturuyor.
    # içine verilen ilk değer formun etiketi, göstereceği yazı oluyor.
    # validators özelliğini forma kısıtlamalar getirmek için kullandık.
    # validators= değerinin içine kontrol edilecek kriterleri liste içinde veriyoruz.
    # validators.Length() verdiğimiz değerlere göre formun min-max eleman sayısını belirledi.
    # validators.Email() formun içine e-posta girilip girilmediğini kontrol ediyor,
    # içine verdiğimiz message değeriyse içindeki değerin valid olmama durumunda ekranda bir mesaj gösteriyor.
    # validators.DataRequired() fonksiyonu formu doldurulması zorunlu hale getiriyor.
    # PasswordField() içine girilen değerin şifre olduğu için ekranda yıldızlı (*) görünmesini sağlıyor.
    # validators.EqualTo() fonksiyonu formun içindeki değerin fieldname="" kısmının içine verilen değere
    # (bu bir değişken, bu durumda confirm'in içine girilen şifre) eşit olup olmadığını kontrol eder,
    # bunu da şifre doğrulama için kullandık.

    # bu formlar hakkında daha detaylı bilgi için internette: WTForms ve Flask-WTForms dokümanlarına bak!

    name = StringField("İsim Soyisim",validators=[validators.Length(min=4,max=25)])
    username = StringField("Kullanıcı Adı",validators=[validators.Length(min=5,max=35)])
    email = StringField("E-Posta Adresi",validators=[validators.Email(message="Lütfen geçerli bir E-Posta adresi giriniz.")])
    password = PasswordField("Parola",validators=[
        validators.DataRequired(message="Lütfen bir parola belirleyin."),
        validators.EqualTo(fieldname="confirm",message="Parolalar uyuşmuyor.")

    ])
    confirm = PasswordField("Parola Doğrulama")

# Register'a benzer bir şekilde LoginForm oluşturduk.
class LoginForm(Form):

    # kullanıcıdan almak için kullanıcı adı ve parola form alanlarını oluşturduk.
    username = StringField("Kullanıcı Adı")
    password = PasswordField("Parola")


app = Flask(__name__)
app.secret_key = "yildizblog"

logout_flash = False

# Veritabanı ile Flask bağlantısı için konfigürasyon ayarları.
app.config["MYSQL_HOST"] = "localhost" # server'a yükleseydik onun bilgilerini girecektik, şimdilik localhost.
app.config["MYSQL_USER"] = "root" # bağlanmak için gerekli kullanıcı adı. xampp'te varsayılan olarak root.
app.config["MYSQL_PASSWORD"] = "" # bağlanmak için gerekli şifre. xampp'te varsayılan olarak boş.
app.config["MYSQL_DB"] = "yildizblog" # bağlanmak istediğimiz veritabanının adı.
app.config["MYSQL_CURSORCLASS"] = "DictCursor" # imleç tipi, verileri sözlük şeklinde almak için DictCursor.

mysql = MySQL(app)


@app.route("/") # Kök dizine request atıldığını algılayacak decorator.
def index(): # Üstünde dekoratör çalışınca devreye girecek fonksiyon

    articles = [ # template içine göndermek için bir sözlük listesi oluşturduk.
        {"id":1,"title":"Deneme1","content":"Deneme1 icerik"},
        {"id":2,"title":"Deneme2","content":"Deneme2 icerik"},
        {"id":3,"title":"Deneme3","content":"Deneme3 icerik"}
    ]

    numbers = [1,2,3,4,5] # template'e göndermek için liste oluşturduk.
    return render_template("index.html",islem = 1, numbers = numbers, articles = articles)
    # render_template fonksiyonu içine verilen html dosyasını renderlayarak sayfaya göndermemizi sağlar.
    # template'te django template'ın if durumu ile kullanmak için bir answer kwarg'ı gönderdik.
    # oluşturduğumuz listeyi bir kwarg olarak template'a gönderdik.


@app.route("/about") # /about dizine request atıldığında aktive olacak decorator.
def about(): # decorator'ün çalıştıracağı fonksiyon.
    return render_template("about.html") # renderlanarak döndürülecek sayfa.


@app.route("/article/<string:id>") # dinamik url yapısı oluşturma
def article(id): # dizindeki id değerini fonksiyonun içine gönderdik.
    cursor = mysql.connection.cursor() # db işlemleri için imleç.
    sorgu = "SELECT * FROM articles WHERE id = %s" # id'si dizindeki id olan makaleyi seçmek için sorgu.
    result = cursor.execute(sorgu,(id,))

    if result > 0: # makale varsa makale detay sayfasına makaleyi gönderip sayfaya yönlendirme.
        article = cursor.fetchone()
        return render_template("article.html",article=article)
    else: # makale yoksa makale bulunamadı sayfasına yönlendirme.
        return render_template("articlenotfound.html",id=id)




# kayıt olma işlemleri
@app.route("/register",methods = ["GET","POST"]) # register sayfasına yönlendirme
# sayfanın hem get request hem de post request metodlarına sahip olduğunu belirtmemiz gerekiyor.

def register():
    # Daha önceden oluşturduğumuz RegisterForm sınıfında bir nesne oluşturduk ve sayfa request'inden
    # form'u çekip nesnenin içine gönderdik.
    form = RegisterForm(request.form)
    # Bu sınıfın içine req.form gönderme kısmını get ve post için ayrı ayrı düşün.

    # POST request atılmışsa ve formdaki bilgiler kısıtlamalara uyuyorsa if koşulu devreye girer.
    if request.method == "POST" and form.validate(): 
        
        name = form.name.data # formun içinde oluşturduğumuz yazı alanlarından verileri çektik.
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data) # şifreyi şifreleyerek çektik.

        verify_sorgu = "SELECT * FROM users WHERE username = %s"

        cursor = mysql.connection.cursor() # veritabanı üstünde işlem yapabilmek için imleç oluşturduk.

        # bu kullanıcı adının zaten kullanılıyor olma ihtimaline karşı önlem.
        result = cursor.execute(verify_sorgu,(username,))

        if result > 0: # kullanıcı adı zaten varsa koşul doğru olacaktır ve burası çalışacaktır.
            # kullanıcı adının kullanımda olduğuna dair flash uyarısı.
            flash("Bu kullanıcı adı zaten alınmış! Başka bir kullanıcı adı deneyin.",category="danger")
            # kayıt sayfasına geri yönlendirme.
            return redirect(url_for("register"))

        else: # kullanıcı adı boştaysa burası çalışacaktır ve yeni kullanıcı veritabanına eklenecektir.

            # SQL sorguları hakkında daha detaylı bilgi için w3schools !
            sorgu = "INSERT INTO users(name,email,username,password) VALUES(%s,%s,%s,%s)"

            # değişik bir formatlama biçimi...
            cursor.execute(sorgu,(name,email,username,password)) # SQL sorgusu çalıştırdık.
            mysql.connection.commit() # DB'de değişiklik yaptığımızda geçerli olması için commit yapılmalı.
            cursor.close() # boş yere kaynak harcamasın diye imleci kapattık.

            # Flash mesajıyla mesajı ve kategorisini gönderdik, bu mesaj bir kez gösterilir.
            flash(f" Başarıyla kayıt oldunuz {name}!","success") 
            
            
            return redirect(url_for("login")) # redirect ile başka sayfaya gönderdik, url_for ile login
                                            # fonksiyonuna sahip olan dizini bulduk.
    else:
        return render_template("register.html",form = form) # Get request durumunda renderlanacak template
        # render'lamak için içine RegisterForm sınıfından oluşturulmuş objeyi de gönderdik.


# /login dizine request atılınca devreye girecek fonksiyon ve dekoratör.
# post request yaparken metodları GET ve POST olarak belirtmeliyiz, yoksa hata verir.
@app.route("/login",methods=["GET","POST"])
def login():
    # oluşturduğumuz LoginForm'un içine request'ten gelen formu atıp bunu form adlı değişkene atadık.
    form = LoginForm(request.form)

    if request.method == "POST": # post request atılmışsa
        username = form.username.data # post request'le gönderilen form'dan verileri çekiyoruz
        password_entered = form.password.data

        cursor = mysql.connection.cursor() # işlem yapmak için database üstünde bir imleç oluşturduk.

        sorgu = "SELECT * FROM users WHERE username = %s" # sorguyu oluşturduk (formatla yapamadım ?)

        # başta config ayarlarında cursorclass = dictcursor belirlemiştik, bu yüzden bu sorgu bize
        # bir sözlük yapısı döndürür.
        result = cursor.execute(sorgu,(username,))

        # eğer kullanıcı adı bulunamazsa fonksiyon 0 dönecektir, burada kullanıcının varlığını kontrol ettik.
        if result > 0: 

            data = cursor.fetchone() # fetch yaparak sözlük şeklinde verimizi data değişkenine atadık.
            real_password = data["password"] # gerçek parolayı şifrelenmiş şekilde sözlükten çektik.

            if sha256_crypt.verify(password_entered,real_password): # şifrelerin uyuştuğunu kontrol ettik.

                flash(f"Başarıyla giriş yapıldı! '{username}'",category="success") # uyuşuyorsa giriş başarılı flash'ı

                session["logged_in"] = True # giriş yapıldığında session (oturum) başlattık.
                session["username"] = username # giriş yapılan kullanıcı adını aldık.

                return redirect(url_for("index")) # anasayfaya dönüş
            
            else: # şifreler uyuşmuyorsa;

                flash(f"'{username}' için şifre hatalı!",category="danger") # şifre hatalı flash'ı
                return redirect(url_for("login")) # login sayfasına dönüş
            
            
        else: # kullanıcı yoksa flash uyarısı patlatıp tekrar login sayfasına döndürülecek.
            flash(f"'{username}' adında bir kullanıcı yok!","danger") # kullanıcı yok flash'ı
            return redirect(url_for("login")) # login sayfasına dönüş

    # html sayfasını renderladık, ve içinde kullandığımız form objesini de beraberinde gönderdik.
    return render_template("login.html",form = form)

@app.route("/logout") # Çıkış Yap butonu bu dizine atıyor ve bu fonksiyon çalışıyor.
@login_required # fonksiyon sadece oturum açılmışsa çalışacak, açılmamışsa giriş sayfasına yönlendirecek,
def logout():   # çünkü login_required decorator'ı bu şekilde yazıldı.
    
    logout_flash_username = session["username"] # flash edilecek kullanıcı adını aldık.
    session.clear() # session'ı (oturum) temizledik ve kapattık.

    flash(f"{logout_flash_username} hesabından çıkış yapıldı.",category="info") # flash'ı gönderdik.
    # flash'ı session.clear()'dan sonra göndermezsek atılan flash da temizlendiği için ekranda gösterilmiyor.

    del logout_flash_username # flash edilecek kullanıcı adını sildik.
    return redirect(url_for("index")) # anasayfaya döndürdük.


@app.route("/articles") # articles sayfasına gidince aktive olacak decorator ve fonksiyon.
def articles():

    cursor = mysql.connection.cursor() # db üstünde işlem yapabilmek için imleç oluşturduk.
    sorgu = "SELECT * FROM articles" # bütün verileri seçme sorgusu.
    result = cursor.execute(sorgu) # eğer veri yoksa 0 dönecektir, varsa başka bir değer dönecektir.

    if result > 0: # veri varsa;
        articles = cursor.fetchall() # bütün makalelerin bilgilerini demet içinde sözlükler şeklinde aldık.
        articles = articles[::-1] # makale tarihlerine göre en sondan sıralansın diye ters çevirdik.
        for article in articles: # makaleler üstünde geziniyoruz.

            # tarihi daha düzgün bir şekilde gösterebilmek için böyle bir şey yaptık,
            # yapmayıp direkt created_date'i kullanarak da aynı şeyi yapabilirdik, düzeltilmeli.
            article["display_date"] = datetime.fromtimestamp(article["created_date"].timestamp())

            # makale uzunluğunu önizleme yaparken kullanmak için aldık.
            article["length"] = len(article["content"])

        # dosyanın içine makaleleri gönderdik ve render'ladık.
        return render_template("articles.html",articles = articles)
    else:
        # makale yoksa direkt render'ladık. dosyanın içinde makale olmadığında göstereceği uyarı zaten yazılı.
        return render_template("articles.html")



@app.route("/dashboard") # makale düzenleme için /dashboard dizinine gidildiğinde aktive olacak fonksiyon.
@login_required # fonksiyon sadece oturum açılmışsa çalışacak, açılmamışsa giriş sayfasına yönlendirecek,
def dashboard():# çünkü login_required decorator'ı bu şekilde yazıldı.

    cursor = mysql.connection.cursor() # verileri almak için imleç.

    # yazar ismi oturum açmış kullanıcı olan makaleleri almak için sorgu.
    sorgu = "SELECT * FROM articles WHERE author = %s" 

    result = cursor.execute(sorgu,(session["username"],)) # veri (makale) yoksa 0 döner, varsa başka.

    if result > 0: # makale varsa;
        articles = cursor.fetchall() # makaleleri aldık.
        return render_template("dashboard.html",articles=articles) # dosyanın içine gönderdik ve render'ladık.
    else: # makale yoksa;
        return render_template("dashboard.html") # render'ladık, makale yok mesajı dosyanın içinde.


# /addarticle dizinine gidince aktive olacak fonksiyon. form da göndereceğimiz için metodlar GET ve POST.
@app.route("/addarticle",methods=["GET","POST"])
@login_required # sadece oturum açıksa yönlendirilir, yoksa giriş sayfasına yönlendirilir.
def addarticle():
    form = ArticleForm(request.form) # önceden oluşturduğumuz sınıfa request.form'u gönderip değişkene atadık.

    if request.method == "POST" and form.validate(): # post request atılmışsa ve form kısıtlamalara uygunsa;
        title = form.title.data # formun başlığını çektik.
        content = form.content.data # formun içeriğini çektik.

        cursor = mysql.connection.cursor() # db'de işlem yapabilmek için bir imleç oluşturduk.
        sorgu = "INSERT INTO articles(title,author,content) VALUES(%s,%s,%s)" # sorguyu yazdık.

        # içine değerleri verip sorguyu çalıştırdık.
        cursor.execute(sorgu,(title,session["username"],content)) 

        mysql.connection.commit() # değişikliklerin geçerli olması için commit yaptık.
        cursor.close() # boşa kaynak harcamasın diye imleci kapattık.

        flash("Makale başarıyla eklendi!",category="success") # kaydedildiğini bildiren flash'ı patlattık.
        return redirect(url_for("dashboard")) # kontrol paneline geri yönlendirdik.


    return render_template("addarticle.html",form=form) # addarticle sayfasına formu gönderdik ve renderladık.

@app.route("/edit/<string:id>",methods=["GET","POST"]) # dinamik url yapısı, get ve post req yapılabilir.
@login_required # oturum açık olmalı.
def edit(id):
    if request.method == "GET": # get req atılmışsa;
        cursor = mysql.connection.cursor() # db'de işlem yapabilmek için imleç.
        sorgu = "SELECT * FROM articles WHERE id = %s AND author = %s"
        result = cursor.execute(sorgu,(id,session["username"]))
        if result == 0: # sorgudan veri elde edilememişse;
            sorgu2 = "SELECT * FROM articles WHERE id = %s" # db'de girilen id'nin aranması için sorgu.
            result2 = cursor.execute(sorgu2,(id,))
            if result2 == 0: # bu id'de bir makale yoksa;
                return render_template("articlenotfound.html",id=id) # makale bulunamadı sayfası
            else:
                flash("Bu makale size ait değil!",category="danger") # makale size ait değil flash'ı.
                return redirect(url_for("index")) # anasayfaya dönüş.
        else: # sorgudan veri elde edilmişse;
            article = cursor.fetchone() # verinin alınması

            # bir form oluşturduk ancak bu formun içine kendimiz zaten db'de olan verileri yerleştireceğiz.
            form = ArticleForm() 

            form.title.data = article["title"] # formun içine db'deki verilerin yerleştirilmesi.
            form.content.data = article["content"]
            return render_template("edit.html",form=form,article=article) # edit sayfasına formun gönderilip render'lanması.


    else: # post request yapılmışsa;
        form = ArticleForm(request.form) # form oluşturduk ve içine post req'ten gelen bilgileri aktardık.

        newTitle = form.title.data # yeni başlık için post req'ten forma aktarılan başlığı çektik.
        newContent = form.content.data # yeni içerik için post req'ten forma aktarılan içeriği çektik.

        sorgu3 = "UPDATE articles SET title = %s,content = %s WHERE id = %s " # güncelleme sorgusu.
        cursor = mysql.connection.cursor() # yeni imleç. neden?
        cursor.execute(sorgu3,(newTitle,newContent,id)) # sorgunun çalıştırılması.
        mysql.connection.commit() # db'de yapılan değişikliğin geçerli olması için commit yapılmalı.
        flash("Makale başarıyla güncellendi!",category="success") # işlemin başarılı olduğuna dair flash.
        return redirect(url_for("dashboard")) # dashboard'a geri yönlendirme.

@app.route("/search",methods=["GET","POST"])
def search():
    if request.method == "GET":
        return redirect(url_for("index"))
    else:

        keyword = request.form.get("keyword")

        cursor = mysql.connection.cursor()

        sorgu = "SELECT * FROM articles WHERE title LIKE '%"+keyword+"%' "

        result = cursor.execute(sorgu)

        if result == 0:
            flash("Aradığınız kelimeye uygun makale bulunamadı...",category="warning")
            return redirect(url_for('articles'))
        else:
            articles = cursor.fetchall()
            for article in articles: # makaleler üstünde geziniyoruz.

                # makale uzunluğunu önizleme yaparken kullanmak için aldık.
                article["length"] = len(article["content"])
            
            articles = articles[::-1]
            return render_template("articles.html",articles=articles)


@app.route("/profile/<string:username>") # kullanıcı adına göre dinamik url oluşturulması.
def profile(username): # fonksiyonun içine dizindeki kullanıcı adını gönderdik.

    cursor = mysql.connection.cursor() # db işlemleri için imleç.

    # adı dizine girilen kullanıcının bilgilerinin alınması için sorgu.
    sorgu = "SELECT * FROM users WHERE username = %s"

    result = cursor.execute(sorgu,(username,)) # sorgunun çalıştırılması.

    if result > 0: # kullanıcı bilgisi dönmüşse;
        user = cursor.fetchone() # bilgilerin alınıp bir değişkene atılması.

        # profili görüntülenen kullanıcıya ait makale bilgilerinin alınması için sorgu.
        sorgu2 = "SELECT * FROM articles WHERE author = %s"
        
        # sorgunun çalıştırılması. (makale gelmemesi durumu profile.html dosyasında kontrol ediliyor.)
        result = cursor.execute(sorgu2,(username,))

        articles = cursor.fetchall() # makale bilgilerinin alınması.
        articles = articles[::-1] # makaleler son tarihten itb. sıralansın diye ters çevirdik.

        for article in articles: # makaleler üstünde geziniyoruz.

            # makale uzunluğunu önizleme yaparken kullanmak için aldık.
            article["length"] = len(article["content"])

        return render_template("profile.html",user=user,articles=articles)

    else: # kullanıcı bilgisi yoksa kullanıcı bulunamadı sayfasına yönlendirme.
        return render_template("profilenotfound.html",username=username)



@app.route("/delete/<string:id>") # dinamik url oluşturma.
@login_required # sayfaya erişmek için oturum açılmış olmalı, bunun için decorator.
def delete(id): # fonksiyonun içine dizindeki id'yi gönderdik.
    cursor = mysql.connection.cursor() # veritabanı üstünde işlem yapabilmek için imleç.

    # yazarı şu an oturum açmış olan yazar ve id'si dizindeki id olan makalenin bilgilerini almak için sorgu.
    sorgu = "SELECT * FROM articles WHERE author = %s AND id = %s"

    result = cursor.execute(sorgu,(session["username"],id))

    if result > 0: # makale yazarı ve id bilgileri uyuşuyorsa makale silinir.
        sorgu2 = "DELETE FROM articles WHERE id = %s" # makale silme sorgusu.
        cursor.execute(sorgu2,(id,)) # sorgunun çalıştırılması.
        mysql.connection.commit() # db'de değişiklik yapan sorguların geçerli olması için commit yapılmalıdır.
        flash(f"{id} numaralı makale başarıyla silindi!",category="success") # flash uyarısı.
        return redirect(url_for("dashboard")) # dashboard'a geri yönlendirme
    else: # bilgiler uyuşmuyorsa;
        sorgu3 = "SELECT * FROM articles WHERE id = %s" # böyle bir makale var mı diye bakmak için sorgu.
        result3 = cursor.execute(sorgu3,(id,))
        if result3 > 0: # varsa
            flash("Bu makale size ait değil!",category="danger") # flash uyarısı.
            return redirect(url_for("index")) # anasayfaya geri yönlendirme.
        else: # yoksa
            return render_template("articlenotfound.html",id = id) # makale bulunamadı sayfası render'lama.



class ArticleForm(Form): # fonksiyonda kullanmak için bir makale formu sınıfı oluşturduk.

    # başlık için bir form satırı
    title = StringField("Makale Başlığı",validators=[validators.Length(min=5,max=100,message="Başlık uzunluğu 5 ile 100 karakter arasında olmalıdır.")])
    
    # içerik için geniş bir yazı alanı.
    content = TextAreaField("Makale İçeriği",validators=[validators.Length(min=10,message="Makale uzunluğu en az 10 karakter olmalıdır.")])



if __name__ == "__main__": # eğer sayfa terminalden çalıştırılırsa __name__ değişkeni __main__ olur ve app çalışır
    app.run(debug=True) # Geliştirirken debug modunu açmak işimizi kolaylaştıracaktır.




