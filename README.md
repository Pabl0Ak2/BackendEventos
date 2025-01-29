# Proyecto de Gestión de Eventos y Boletos

Este proyecto es una aplicación para gestionar eventos, vender boletos y canjearlos, implementada en Python utilizando Flask como framework web y MySQL como base de datos.

## Requisitos

### 1. Instalación de MySQL
Para comenzar a utilizar el proyecto, necesitas tener instalado **MySQL**. Puedes seguir los siguientes pasos:

1. Descarga e instala MySQL desde [MySQL Downloads](https://dev.mysql.com/downloads/).
2. Asegúrate de tener MySQL corriendo y accesible en tu máquina local (por defecto, usa el puerto 3306).
3. Crea la base de datos y las tablas ejecutando el siguiente script en MySQL:

    ```sql
    CREATE DATABASE sistema_ticket;

    USE sistema_ticket;

    CREATE TABLE eventos (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        start_date DATETIME NOT NULL,
        end_date DATETIME NOT NULL,
        total_tickets INT NOT NULL CHECK (total_tickets BETWEEN 1 AND 300),
        sold_tickets INT DEFAULT 0 NOT NULL
    );

    CREATE TABLE boletos (
        id INT AUTO_INCREMENT PRIMARY KEY,
        event_id INT,
        ticket_code VARCHAR(255) UNIQUE NOT NULL,
        is_claimed BOOLEAN DEFAULT FALSE,
        claim_date DATETIME,
        FOREIGN KEY (event_id) REFERENCES eventos(id)
    );
    ```

### 2. Instalación de Python
Este proyecto fue desarrollado usando **Python**. Para instalar Python, sigue estos pasos:

1. Descarga Python desde [python.org](https://www.python.org/downloads/).
2. Asegúrate de tener Python 3.x instalado.
3. Verifica la instalación con:

    ```bash
    python --version
    ```

### 3. Instalación de dependencias de Python
El proyecto usa Flask y otras bibliotecas. Para instalarlas, sigue estos pasos:

1. Crea un entorno virtual (opcional, pero recomendado):

    ```bash
    python -m venv venv
    ```

2. Activa el entorno virtual:

    - En Windows:

      ```bash
      .\venv\Scripts\activate
      ```

    - En Mac/Linux:

      ```bash
      source venv/bin/activate
      ```

3. Instala las dependencias necesarias ejecutando el siguiente comando en la terminal:

    ```bash
    pip install Flask
    ```

    Si no tienes el archivo `requirements.txt`, puedes instalar las dependencias manualmente con:

    ```bash
    pip install mysql-connector-python flask flask_cors uuid python-dateutil
    ```

### 4. Ejecutando el proyecto
Para ejecutar el proyecto, asegúrate de que MySQL esté corriendo y que tu base de datos esté configurada correctamente.

1. Entra al directorio del proyecto y ejecuta el siguiente comando:

    ```bash
    python app.py
    ```

2. El servidor de Flask debería estar corriendo en [http://localhost:5000](http://localhost:5000).

### Requerimientos de Python
Este proyecto utiliza las siguientes bibliotecas:

- `mysql-connector-python`: Para conectar Flask con la base de datos MySQL.
- `flask`: Framework web para la aplicación backend.
- `flask_cors`: Para habilitar CORS (Cross-Origin Resource Sharing) en la API.
- `uuid`: Para generar códigos de boletos únicos.
- `python-dateutil`: Para el manejo de fechas de forma flexible.
- `jsonify`: Para generar respuestas JSON.
- `request`: Para obtener datos del cuerpo de las solicitudes.

#### Puedes instalar todas estas dependencias con el siguiente comando:

```bash
pip install mysql-connector-python flask flask_cors uuid python-dateutil
