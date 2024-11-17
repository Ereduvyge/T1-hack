# T1-hackthon
  
## Инструкция по запуску приложения с помощью Докер контейнера  
  

Создать образ с помощью команды:

    docker build --build-arg APP_ENV=production -t hackathon .

  

Запустить приложение с помощью команды:

    docker run -p 8080:8080 -t hackathon

  

Приложение будет доступно по адресу `localhost:8080`
