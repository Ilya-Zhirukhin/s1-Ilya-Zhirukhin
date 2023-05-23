/* Client script */


//Код представляет собой JavaScript-скрипт, который выполняет следующие действия:
//
// 1. Устанавливается масштабирование страницы с помощью свойства `zoom` для тела документа. Значение 0.8 устанавливает масштаб 80% от исходного размера страницы.
//
// 2. Создаются переменные `app_container` и `app_body`, которые представляют собой элементы DOM на странице.
//
// 3. Инициализируется переменная `selected_page` со значением `null`, которая будет использоваться для отслеживания текущей выбранной страницы.
//
// 4. Создается объект сокета `socket` с использованием URL-адреса сервера, на котором работает сокет.
//
// 5. При установлении соединения с сервером выводится сообщение в консоль.
//
// 6. При загрузке документа (событие `document.ready`) устанавливается обработчик клика на элементы с классом `w3-bar-item` внутри `#mySidebar`.
//
// 7. В обработчике клика проверяется, является ли текущий элемент клика (`this`) выбранной страницей (сравнивается атрибут `name` элемента с `selected_page`).
//
// 8. Если текущий элемент не является выбранной страницей, выполняется AJAX-запрос к серверу с использованием URL-адреса `/app/` и имени выбранной страницы.
//
// 9. При успешном выполнении AJAX-запроса результат помещается в контейнер `app_container`, класс `selected_item` добавляется к выбранному элементу, и у всех остальных элементов класс `selected_item` удаляется.
//
// 10. Устанавливается обработчик события `submit` для формы с идентификатором `joinclassform`.
//
// 11. В обработчике события `submit` предотвращается отправка формы по умолчанию.
//
// 12. Выполняется AJAX-запрос к серверу с данными, введенными в форму, и URL-адресом `/join-team`.
//
// 13. При получении ответа от сервера обрабатывается результат. Если присутствует ошибка, выводится сообщение об ошибке и отображается соответствующее уведомление.
//
// 14. Если ответ не содержит ошибки, в элемент `#menulist` добавляется новый элемент списка с информацией о комнате. Затем с помощью сокета отправляется сообщение `join-room` с идентификатором комнаты.
//
// 15. Устанавливается обработчик события `submit` для формы с идентификатором `teamcreationform`.
//
// 16. В обработчике события `submit` выполняется AJAX-запрос к серверу с данными, введенными в форму, и URL-адресом `/create-team`.
//
// 17. При получении ответа от сервера обрабатывается результат
//
// . Если присутствует ошибка, выводится сообщение об ошибке и отображается соответствующее уведомление.
//
// 18. Если ответ не содержит ошибки, отображается уведомление об успешном создании комнаты и отправляется сообщение `join-room` с идентификатором новой комнаты.
//
// 19. Устанавливаются обработчики событий для открытия модальных окон `#teammodal` и `#joinclass_modal`, а также для закрытия меню настроек `#classroom_settings`.
//


// Установка масштаба страницы
document.body.style.zoom = 1;

// Получение элементов страницы
const app_container = $('#app_container');
const app_body = app_container.children("#app_body");

// Инициализация переменной для выбранной страницы
let selected_page = null;

// Подключение к серверу с помощью Socket.IO
const socket = io('http://' + document.domain + ':' + location.port, {transports: ['websocket']});
socket.on('connect', function () {
	console.log("Connected to the network server.");
});

// Обработка клика по элементу в боковой панели
$(document).ready(function () {
	$('#mySidebar .w3-bar-item').on('click', function (event) {
		let this_element = this;
		// Проверка, выбрана ли уже эта страница
		if ($(this).attr('name') !== selected_page) {
			selected_page = $(this).attr('name');
			// Отправка AJAX-запроса на сервер для получения контента страницы
			$.ajax({url: '/app/' + $(this).attr('name'), type: 'POST'}).done(function (data) {
				// Заполнение контейнера приложения полученным контентом
				app_container.html(data);
				$(this_element).addClass('selected_item');
				$('#mySidebar > .w3-bar-item').each(function (index) {
					if (this !== this_element) {
						$(this).removeClass('selected_item');
					}
				});
			});
		}
	});

	// Обработка отправки формы для присоединения к команде
	$('#joinclassform').on('submit', function (event) {
		event.preventDefault();
		// Отправка AJAX-запроса на сервер с кодом команды
		$.ajax({data: {code: $('#classroom_code').val()}, type: 'POST', url: '/join-team'}).done(function (data) {
			if (data.error) {
				console.log(data.error);
				$('#join_notice').css('display', 'block');
				$('#join_notice').html(data.error);
			} else {
				// Добавление элемента команды в список и подключение к комнате Socket.IO
				$('#menulist').append(`<div><a class="w3-bar-item w3-button classroom" id='%${data.result.id}' style='text-decoration: none; width:100%'><img src="${data.url_for_img}" width=25></img> ${data.result.name} <i class='fas fa-cog float-right'></i></a><ul class="channels"></ul></div>`);
				socket.emit('join-room', data.result.id);
			}
		});
	});

	// Обработка отправки формы для создания команды
	$('#teamcreationform').on('submit', function (event) {
		// Отправка AJAX-запроса на сервер с данными о команде
		$.ajax({
			data: {
				team_name: $('#teamname').val(),
				team_description: $('#teamdescription').val()
			},
			type: 'POST',
			url: '/create-team'
		}).done(function (data) {
			const notice_field = $('#notice');
			if (data.error) {
				// Отображение ошибки при создании команды
				notice_field.html(data.error);
				notice_field.addClass('alert-danger');
				notice_field.css('display', 'block');
				console.log("error: team was not created due to the following < " + data.error + " >");
			} else {
				// Отображение успешного сообщения о создании команды
				notice_field.css('display', 'block');
				notice_field.addClass('alert-success');
				notice_field.html("classroom `" + $('#teamname').val() + "` has been created.");
				socket.emit('join-room', data.new_classroom.id);
				$('#teamname').val('');
				$('#teamdescription').val('');
				setTimeout(() => {
					notice_field.html('');
					notice_field.hide();
					$("#teammodal").hide();
				}, 1624);
				if ($('#classrooms').hasClass('selected_item')) {
					// Добавление элемента команды в список
					$('#menulist').append(`<div><a class='classroom w3-bar-item w3-button' style='text-decoration: none; width:100%' id="%${data.new_classroom.id}"><img src=${data.new_classroom.imgurl} width=25> ${data.new_classroom.name} <i class='fas fa-cog float-right'></i></a><ul class='channels'></ul></div>`);
				}
			}
		});
		event.preventDefault();
	});
});

// Функции для отображения и скрытия модальных окон
const toggle_class_creator = () => {
	$('#teammodal').css('display', 'block');
	$('#teammodal').find('.alert').css('display', 'none');
}

const toggle_class_join = () => {
	$('#joinclass_modal').css('display', 'block');
	$('#join_notice').css('display', 'none');
}

const close_settings_menu = () => {
	$('#classroom_settings').css('width', '0%');
}


