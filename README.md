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

### Instalar dependencias

Ejecuta los siguientes comandos:

```
python -m venv .venv
source ./.venv/bin.activation
pip install -r ./requirements.txt
```

---

Ejecuta el siguiente comando:

```
python app.py
```

Luego de ejecutar el comando indicado arriba, la terminal o CMD debería haberte devuelto en la salida los IDs, nombre de la imagen, estado y el puerto (entre otros datos) de los 3 contenedores. En caso de haber sido así, felicidades, has configurado correctamente tu entorno de trabajo :)

Para comprobar que la aplicación esté corriendo correctamente, introduce la siguiente dirección URL en tu navegador web de preferencia:

> http://localhost:<puerto>/hello_world

Deberías ver renderizado en tu navegador el siguiente archivo json:

```
{
  "message": "Hello World from python3 and Flask"
}
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
