# romulo-api

---

### Variables de entorno

```
# App config
app_port=<Puerto de la aplicación>
pwd_rounds=<Rondas de encriptación de contraseña>
mode=<Modo de desarrollo> ["debug"|"release"]

# Database config
db_user=<Usuario de la base de datos>
db_password=<Contraseña de la base de datos>
db_name=<Nombre de la base de datos>
db_host=<Host de postgresql>

# JWT
jwt_password=<Llave de los tokens de autorización>

# Email config
otp_email=<Correo electrónico>
otp_password=<Contraseña>
otp_smtp=<cadena smtp>
otp_port=<puerto smtp>
otp_secret=<Clave secreta de la sesión>
```

---

#### Guía de instalación y desarrollo

---

## Configurar entorno de trabajo

### Git

Para comenzar, instala el sistema de control de versiones git en tu máquina local usando el siguiente comando (linux)

#### Para sistemas operativos basados en Debian y Ubuntu:

```
sudo apt update
sudo apt install git
```

#### Para sistemas operativos basados en Arch

```
sudo pacman -S git
```

### Para sistemas operativos Windows y MacOS

Ingresa al sitio web oficial de git y descarga el instalador. Copia y pega la siguiente dirección URL en tu navegador web de preferencia:

> https://git-scm.com/

#### Configura git en tu máquina local

Ejecuta los siguientes comando en tu terminal o CMD para configurar git, los comandos son exactamento los mismos para cualquier sistema operativo:

```
git config --global user.name "<Nombre de usuario>"
git config --global user.email "<Correo electrónico de github>"
```

Reemplaza el contenido dentro de los corchetes angulares por tu información. Por supuesto, no incluyas tampoco los símbolos de corchetes angulares, al menos que tu intención sea que te salte un error.

### Docker

Descarga e instala docker desktop en tu máquina local desde su sitio web oficial:

> https://www.docker.com/

También puedes instalar únicamente docker engine, personalmente prefiero usar la herramienta de línea de comandos antes que la aplicación gráfica. Igualmente, docker engine está incluido en el software Docker desktop, lo que significa que al instalar Docker desktop también tendrás la herramienta de línea de comandos.

Sigue las indicaciones de la documentación de Docker para instalarlo, de igual manera no tiene mayores complicaciones. Si te pierdes, siempre tendrás tus dudas respondidas en la documentación de Docker o en Stack Overflow ;)

#### Nota

> Si Docker engine tiene problemas para iniciar correctamente, comprueba que tienes habilitado el soporte para virtualización. Algunas veces la virtualización está desactivada en la BIOS o UEFI, debes activarla para que Docker engine pueda funcionar correctamente.

---

## Clonar el repositorio

Abre la terminal o CMD y ubícate en el directorio de tu sistema operativo dónde deseas almacenar el código fuente de la API:

```
cd /ruta/del/directorio
```

Posteriormente, copia y pega en la terminal el siguiente comando

```
git clone https://github.com/edgarchacinweb/romulo-api.git
```

---

## Construir imagen de Docker

Una vez hayas instalado Git, Docker Engine y/o Docker Desktop, y hayas clonado el repositorio correctamente deberás construir la imange de docker de la aplicación. Una imagen de Docker, o una imagen de contenedor, es un archivo ejecutable e independiente que se utiliza para crear un contenedor.

Los contenedores de Docker nos permiten crear un entorno de desarrollo aislado independiente de nuestra máquina, este entorno aislado ya viene configurado para ejecutar la aplicación o desarrollarla sin tener que preocuparnos de instalar software externo manualmente, de esta forma, todos los desarrolladores del equipo tendrán el mismo entorno para desarrollar y ejecutar la aplicación. De esta forma, con las imágenes y contenedores de Docker podemos evitar incompatibilidades entre versiones, sistema operativo, configuración de la máquina, etc que puedan interferir en el desarrollo o correcta ejecución de la aplicación.

Ya conociendo una breve descripción de las imágenes y contenedores de Docker, podemos construir la imagen de la aplicación escribiendo un simple comando en la terminal o CMD:

```
docker build -t romulo_api_app:latest .
```

### NOTA

> El anterior comando se debe ejecutar en el directorio que contenga el archivo Dockerfile, de lo contrario, verás que el Docker Engine te devuelve un error. Navega con la terminal o CMD usando el comando cd para ubicarte en el directorio que contiene el Dockerfile y ejecuta el comando.

### Posibles errores

> En el caso de recibir un error que diga algo parecido a: docker no se reconoce como un comando interno o externo (dependiendo del sistema operativo puede ser un mensaje de error ligeramente diferente), asegúrate que el Docker Engine esté correctamente instalado en tu máquina.

> En el caso de recibir un error relacionado con el Dockerfile deberás reportar el problema al administrador de la imagen de Docker.

> En el caso de linux, es probable que debas ejecutar el comando con permisos de administrador utilizando el comando sudo antes de docker. Este comportamiento se puede evitar realizando ciertas configuraciones especificadas en el siguiente enlace: https://docs.docker.com/engine/install/linux-postinstall/

---

## Creando y corriendo contenedor de Docker

Luego de haber construido la imagen correctamente la imagen escribe el siguiente comando en la terminal o CMD:

```
docker image ls
```

Si la terminal o CMD te devuelve en la salida el siguiente resultado significa que la imagen se creó correctamente:

```
REPOSITORY       TAG       IMAGE ID       CREATED          SIZE
romulo_api_app   latest    07f39136530f   24 minutes ago   1.01GB
```

#### NOTA

> El campo "IMAGE ID" no será idéntico al IMAGE ID que docker generará para identificar la imagen que creaste. Este comportamiento es correcto, ya que el IMAGE ID es un identificador único que usará docker para localizar tu imagen. Esto es igual para los contenedores, cada vez que construyas una nueva imagen o un nuevo contenedor docker generará un ID diferente.

Posteriormente, utiliza el comando cd para ubicarte en el directorio dónde se encuentra el archivo docker-compose.yml, que en caso de haber clonado el repositorio correctamente estará en el mismo directorio dónde se encuentra el archivo Dockerfile. Ejecuta el siguiente comando para crear y correr el repositorio:

```
docker compose up -d
```

Si es la primera vez que ejecutas este comando verás que se están descargando vários archivos, este comportamiento es correcto, no te preocupes.

Luego de terminar de crear los 3 siguientes contenedores:

- Contenedor de la base de datos PostgreSQL.
- Contenedor de pgAdmin.
- contenedor de la aplicación.

Ejecuta el siguiente comando:

```
docker ps
```

Luego de ejecutar el comando indicado arriba, la terminal o CMD debería haberte devuelto en la salida los IDs, nombre de la imagen, estado y el puerto (entre otros datos) de los 3 contenedores. En caso de haber sido así, felicidades, has configurado correctamente tu entorno de trabajo :)

Para comprobar que la aplicación esté corriendo correctamente, introduce la siguiente dirección URL en tu navegador web de preferencia:

> http://localhost:5000/hello_world

Deberías ver renderizado en tu navegador el siguiente archivo json:

```
{
  "message": "Hello World from python3 and Flask"
}
```

En caso de no ver el resultado esperado, revisa que el puerto 5000 no está siendo ocupado por otro proceso. También puedes escribir el siguiente comando para ver los logs del contenedor, en caso de algún error estos se serán registrados en los logs.

```
docker logs <ID del contenedor>
```

Puedes conseguir el ID del contenedor ejecutando el siguiente comando:

```
docker container ls
```

---

### Configurando Visual Studio Code

Para comenzar a desarrollar, descarga las siguientes extensiones de visual studio code:

- [Docker](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-docker)
- [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

Si los contenedores de Docker están corriendo correctamente, haz clic en el botón azúl que está ubicado en la esquina inferior izquiera. Posteriormente, selecciona la opción:

> Attach to Running Container...

Si no ves ningún mensaje de error y se despliega otra lista, selecciona la siguiente opción:

> /romulo_api

Inmediatamente se abrirá otra instancia de Visual Studio Code (o al menos debería ser así). Descarga las siguientes extensiones de Visual Studio Code:

- [Python](https://marketplace.visualstudio.com/items?itemName=ms-python.python)
- [Python Debugger](https://marketplace.visualstudio.com/items?itemName=ms-python.debugpy)
- [Error Lens](https://marketplace.visualstudio.com/items?itemName=usernamehw.errorlens)

Puedes modificar cualquier archivo, al guardar los cambios estos se verán reflejados en el proyecto automáticamente :)

---

## Configurar base de datos

Luego de haber configurado correctamente tú entorno de desarrollo (entiendase "correctamente" cómo no te salió ningún error raro en el proceso o lograste resolverlos), deberás configurar la base de datos PostgreSQL. Actualmente la base de datos ya está creada, sin embargo, estás no cuenta con la estructura que requiere la aplicación para funcionar.

Para configurar la base de datos, abre tu navegador web preferido e ingresa la siguiente dirección URL:

> http://localhost:8080

### NOTA

> Si ocurre algún error inesperado, asegúrate de que el puerto 8080 de tú máquina esté libre antes de correr los contenedores.

Escribe las siguientes credenciales para iniciar sesión:

```
Email Address: romulo@dev.com
Password: romulo12345
```

Posteriormente, registre un nuevo servidor en pgAdmin con los siguientes datos:

```
Name: romulo_db
Host name: postgres
Port: 5432
Maintenance database: romulo_app
username: root
Password: romulo12345
```

### Nota

> En caso de un error verifique el puerto 5432 de tú máquina esté libre antes de correr el contenedor.

Expande el servidor romulo_db, posteriormente presiona la combinación de teclas [Alt]+[Shift]+[Q].

Copia el contenido del archivo database.sql (debería estar en el mismo directorio que el archivo Dockerfile y docker-compose.yml), pega el contenido en el cuadro de texto, selecciona todo y posteriormente ejecuta la consulta sql presionando la tecla [F5].

Listo, has configurado la base de datos correctamente.

---

## Comandos básicos de git

### git add [archivo a subir]

Este comando se utiliza para agregar cambios al área de stagging, este paso es obligatorio para posteriormente subir los cambios al repositorio.

```
git add .
```

En este caso, el "." al final del comando significa que agregará todos los cambios al área de stagging.

### git status

Este comando se utiliza para mostrar el estado del directorio de trabajo y el área de stagging.

```
git status
```

### git commit

Esto comando sirve para guardar los cambios agregados previamente en el área de stagging.

```
git commit [-m "<mensaje>"]
```

Si no agregamos la bandera m, git abrirá un editor de texto de terminal, normalmente usará el editor vi. Sólo tienes que escribir un mensaje para el commit (procura que sea corto y preciso, debe describir exactamente los cambios importantes que se hicieron en el proyecto)

### git push

Este comando sirve para enviar el commit al repositorio remoto, en este caso será Github. Si el repositorio es privado (como en este caso) le solicitará al desarrollador un token, de esta forma Github se asegurará que sólo los desarrolladores del proyecto puedan hacer cambios. Para obtener el token debes pedirselo al administrador del repositorio.

```
git push -u origin [rama]
```

"-u origin" significa que vamos a subir los cambios a una rama específica. La rama principal del proyecto es main, pero también puedes subir cambios a la rama en la que te encuentras trabajando.

### git branch

Este comando se usa para crear nuevas ramas. Las ramas en git sirven para organizar de mejor manera los cambios. Imaginate que te toca desarrollar "x" funcionalidad de la aplicación, en este momento el código alojado en la rama "main" se encuentra se encuentra funcionando, al crear una rama distinta podrás subir cambios al repositorio sin alterar el código de la rama principal. De esta forma, si haces un cambio que comprometa el correcto funcionamiento de la aplicación, estos cambios no afectarán a la rama principal.

```
git branch [nombre de la rama]
```

### git checkout

Este comando sirve para cambiar de ramas de git, además de permitir al desarrollador volver a una versión anterior del archivo así este haya sido modificado várias veces.

```
git checkout [rama|commit id]
```

Si utilizas un "commit id" en vez de una rama, este volverá al estado del archivo o repositorio en el que se encontraba ese commit.

### git log

Este comando sirve para acceder al historio de commits

```
git log [-p|--name-only|--one-line]
```

El comando git log acepta múltiples banderas con las que puedes especificar el comportamiento deseado.

#### Banderas más útiles

- **-p**: Muestra los cambios introducidos en cada commit.
- **-name-only**: Muestra sólo los nombres de los archivos modificados.
- **--one-line**: Muestra una línea por commit, con el hash abreviado y el mensaje del commit.

---

### Comandos básicos de docker

#### Apagar contenedor de docker

> docker container stop [id del contenedor]

#### Mostrar contenedores corriendo

> docker ps
> docker container ls

Ambos comandos sirven para lo mismo

#### Mostrar contenedores inactivos

> docker container ls -l

#### Eliminar contenedores

> docker container rm [id...]

Puedes eliminar varios contenedores al mismo tiempo escribiendo su id y dejando un espacio por cada ID de contenedor.

#### Eliminar todos los contenedores

> docker container prune

#### Crear una imagen

> docker build -t [nombre de la imagen][:etiqueta] [directorio del Dockerfile]

Este comando requiere del archivo Dockerfile correctamente configurado. la bandera -t sirve para establecer un nombre para la imagen, el nombre no debe contener espacios en blanco ni caracteres especiales, seguido de la version (si no especificas la versión docker definirá latest por defecto). Por último, debes especificar el directorio dónde se encuentra el archivo Dockerfile.

##### NOTA

> Si escribes un "." al final del comando le estarás diciendo a docker que el archivo Dockerfile se encuentra en el mismo directorio dónde estas ubicado.

#### Mostrar imagenes

> docker image ls

#### Eliminar una imagen o várias imágenes

> docker image rm [id...]

#### Eliminar todas las imágenes

> docker image prune

#### Crear contenedores con docker compose

> docker compose up [-d]

##### NOTA

> La bandera -d es opcional, sirve para especificar que la ejecución de los contenedores será ajena a la terminal. Es decir, podrás cerrar la terminal y los contenedores seguirán corriendo.

#### Apagar contenedores con docker compose

> docker compose down

Este comando apaga y elimina todos los contenedores creados con el archivo docker-compose.yml.
