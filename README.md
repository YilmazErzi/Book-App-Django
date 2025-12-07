This project, developed as part of my graduation project, is an e-commerce site that offers personalized book recommendations. It provides daily book recommendations and price information. Users can receive personalized recommendations using the integrated AI model. They can also view reviews of these recommendations and add any book they want to their cart.

Django, Bootstrap, Python, and HTML were used in the project.
Applications included in the project:

Book_app is the main settings folder. Settings.py contains general settings, while urls.py contains the main URL scheme.

The Account application was added for personal transactions. Operations such as registration, login, and password changes are performed through this application.

The Cart application was added for cart transactions. Operations such as add to cart, delete from cart, view cart, and checkout were defined under this application.

The Data folder contains the dataset and model we use in our AI studies.

The data_api application contains the code for the API added to the project. Every time you visit the website, it randomly suggests books. We add these books to the database via the API. Operations for deleting, listing, and updating books are also defined within this application.

The indexes application contains the main pages, such as home.html, about.html, and contact.html. The website's main functions and artificial intelligence operations are defined within this application.

The myenv folder contains the virtual environment. The necessary libraries are installed in the virtual environment and are also specified in requirements.txt.

The templates folder contains the HTML files containing the outlines that appear on each page.

The file we used for model training is "model_egit.py." "test_model.py" was used for testing the model.

The database used is SQlite, the default database in Django.

Note: This project was primarily implemented with the help of a Django web development course offered by BTK Academy.

Advisor: Hilal Haznedar
Developers:
Yılmaz Erzi
Ömer Taha İşler
