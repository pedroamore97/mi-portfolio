### **Gestor de Portfolio de Inversión**

Este es un gestor de portfolio de inversión en tiempo real construido con **Python** y la librería **Streamlit**. La aplicación te permite rastrear y analizar el rendimiento de tus activos, incluyendo **acciones** y **criptomonedas**.

📈 **Características principales:**

* **Análisis en tiempo real:** Obtén precios actualizados de tus activos a través de la API de **Yahoo Finance**.
* **Gestión de cartera:** Añade o elimina acciones y criptomonedas, especificando la cantidad, el precio de compra y la divisa.
* **Visualización de datos:** Ve la distribución de tu portfolio con gráficos circulares interactivos.
* **Métricas de rendimiento:** Consulta el valor total de tu cartera, tu inversión inicial y la rentabilidad (ganancias/pérdidas) de cada activo.
* **Persistencia de datos:** Los datos de tu portfolio se guardan en una base de datos local SQLite (`precios_portfolio.db`).

---

### **Tecnologías utilizadas**

* **Python:** Lenguaje de programación principal.
* **Streamlit:** Framework para construir la interfaz de usuario de la aplicación.
* **yfinance:** Librería para obtener datos financieros de Yahoo Finance.
* **pandas:** Para la manipulación y análisis de datos.
* **plotly.express:** Para la creación de gráficos interactivos.
* **sqlite3:** Módulo para la gestión de la base de datos local.

---

### **Cómo ejecutar el proyecto localmente**

Sigue estos pasos para correr la aplicación en tu propio ordenador:

1.  **Clona el repositorio:** Abre tu terminal y ejecuta el siguiente comando:
    ```bash
    git clone [https://github.com/tu_usuario/tu_repositorio.git](https://github.com/tu_usuario/tu_repositorio.git)
    cd tu_repositorio
    ```
    *(Asegúrate de reemplazar `tu_usuario/tu_repositorio` con la dirección de tu repositorio)*

2.  **Crea un entorno virtual (opcional pero recomendado):**
    ```bash
    python -m venv venv_bolsa
    source venv_bolsa/bin/activate  # En Windows usa `venv_bolsa\Scripts\activate`
    ```

3.  **Instala las dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Ejecuta la aplicación:**
    ```bash
    streamlit run PORTFOLIO.py
    ```

La aplicación se abrirá automáticamente en tu navegador web.

---

### **Uso**

Una vez que la aplicación esté corriendo, utiliza la barra lateral para añadir tus activos, tanto acciones como criptomonedas. Los datos se guardarán automáticamente. Podrás ver el resumen de tu portfolio y los detalles de cada activo en la sección principal del dashboard.