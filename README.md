KÖVETELMÉNYEK:
    LinuxOS (Ajánlott pl.Én Kubuntu24.04 et használok a suliban)
    Git
    Docker 
    Docker Compose
    PostgreSQL

    Windows alatt is ugyanúgy működik a .sh fájlokban lévő parancsokat kell használni , de ezek eltérhetnek a linuxostól .

SETUP: 
   0. Adjunk meg minden jogot a felhasználónknak a könyvtár tartalmához --->
   parancs a Vizsgaremek/ könyvtárban: sudo ./permission.sh
   1. bash --> sudo build.sh (Ez letölt minden szükséged dolgot és lebuildeli a programunkat. Ezt csak először kell mentenni , vagy akkor ha új csomagot tettünk a requirements-source.txt -be)
   2. bash --> sudo ./start.sh (itt látod a konzolodban a request-eket és mindent , ami futásidőben történik . Ja és ezt a parancs az esetek 99% - ában elfüstöl , olyankor CTRL + C és futtatsd újra a scriptet.)
   Ha nem kapcsolódik a postresql adatbázis , annak az az oka , hogy az adatbázis volume létrejött , de maga az adatbázis nem . 
   Hozzuk létre. bash --> sudo ./database.sh
   3. Új bash --> sudo ./shell.sh (itt tudsz a programra vonatkozó parancsokat , utasításokat kiadni futásidőben)
   4. Ha szeretnénk a Docker containerbe eszközöket akkor most megtehetjük , parancs: apt-get update apt-get install -y mc
   5. Az újonnan megnyilt bashban a parancs ./manage.py createsuperuser . Aaztán ./manage.py makemigration . Aztán ./manage.py migrate .  


KÖNYVTÁR: 
    - .sh fájlok : A bashscriptekkel parancsokat adhatunk ki , így nem kell mindig begépelnünk azokat 
    - Dockerfile : Tartalmazza buildeléshez szükséges alapadatokat 
    - docker-compose.yml : Tartalmazza azokat az adatokat , amelyek ahhoz szükségesek , hogy a conatinerben futhasson a backend .
    - requirements-sorce.txt : A függőségek fő könyvtárainak neve 
    - requirements:txt : Az összes függőség
    - sample.env : Környezeti változók pl. : secret key , jelszó , access token !!!!!!!!!!!!!!! Soha nem kerülhet ki ez a fájl az internetre !!!!!!!!!!!!!!!!!!!!!
    (ez a fájl a helyi gépen .env nem sample.env )
    - conf könyvtár : ez tartalmazza a konfigurációhoz szükséges .env fájl , erre is ugyanaz vonatkozik !
    - api könyvtár : ez tartalmazza az projekt és a applikáció könyvtárát

