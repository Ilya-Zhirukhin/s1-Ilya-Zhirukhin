selected_channel = null;
selected_classroom = null;
const clear_chatbox = () => {
    const chat_box = $('#channel_display .messagescontainer').first();
    chat_box.html('');
}
const set_chat_title = (server_title, channel_title) => {
    const chat_title = $('#channel_display .upper_part .title').first(); //getting the first h4 element inside of the channel_display element
    chat_title.html(`<b>${server_title}</b> ${channel_title}`);
    $(chat_title).find('i').remove();
}
const clear_submissions = () => {
    $('#submissions').html('');
}
const add_message = (message_data) => {
    const chat_box = $('#channel_display .messagescontainer').first();
    chat_box.append(`<div class="message bg-light"><span><b>${message_data.author.name}</b> ${message_data.date}</span><p>${message_data.content}</p></div>`);
    $(chat_box).scrollTop(10000);
}
const clear_notes = () => {
    const notes = $('#note-container');
    const notes_list = $('#note-list');
    notes.html('');
    notes_list.html('');
}
const add_note = (note_data, active) => {
    const note_list = $('#note-list');
    const note_container = $('#note-container');
    let id = note_data.note_title.replaceAll(' ', '') + note_data.note_id.toString(10);
    note_list.append(`<a class="list-group-item list-group-item-action ${active}" data-toggle="list" href="#${id}" role="tab" style='z-index:0;'>${note_data.note_title}</a>`);
    additional_text = '';
    if (note_data.note_img) {
        additional_text += `<img src="${note_data.note_img}" style='max-width:600px; max-height:600px;' />`;
    }
    note_container.append(`<div class="tab-pane ${active}" id="${id}" role="tabpanel">${additional_text}<p>${note_data.note_text}</p></div>`);
}


const add_assignment = (assignment_data, is_super) => {
    const assignment_list = $('#assignments-list');
    if (assignment_data.id) {
        if (is_super) {
            assignment_list.append(`<tr value=${assignment_data.id}><td>${assignment_data.text}</td><td>${assignment_data.duedate}</td><td><button class='show_submission_button' data-target='#submissions'>View submissions</button> </td> </tr>`);
        } else {
            if (assignment_data.submission_state) {
                assignment_list.append(`<tr value=${assignment_data.id}><td>${assignment_data.text}</td><td>${assignment_data.duedate}</td><td>Already submitted</td> </tr>`);
            } else {
                assignment_list.append(`<tr value=${assignment_data.id}><td>${assignment_data.text}</td><td>${assignment_data.duedate}</td><td><form id='homework_submission'><input type=file name=homework><button>submit</button></form></td></tr>`);

            }
        }
    }
}
const clear_assignments = () => {
    const assignment_list = $('#assignments-list');
    assignment_list.html('');
}
const toggle_submissions_menu = () => {
    $('#testest').css('display', 'block');
}
$(document).ready(function () {
    $('body').click(function (e) {
        var target = $(e.target);
        if (!target.is('#new_conversation_form') && !target.is('#new_conversation_form input')) {
            is_visible = $('#new_conversation_form').css('display');
            if (is_visible !== 'none') {
                $('#new_conversation_form').css('display', 'none');
                $('#newconversation').css('display', 'block');
            }
        }
    });
    $(document).on('submit', '#note_form', function (event) {
        let form_data = new FormData($('#note_form')[0]);
        form_data.append('channel_id', selected_channel);
        event.preventDefault();
        if (selected_channel != null) {
            $.ajax({
                data: form_data,
                contentType: false,
                processData: false,
                url: 'add-note',
                method: 'POST'
            }).done(function (data) {
                $("#note_form").trigger("reset");
                add_note(data['new_note'], '');
            });
        }
    });
    $(document).on('click', '#menulist .classroom', function () {
        let id = parseInt($(this).attr('id').slice(1, $(this).attr('id').length), 10);
        selected_classroom = id;
        $.ajax({url: `retrieve-channels/${id}`, type: 'POST'}).done((data) => {
            console.log(data);
            if (data['result'].length > 0) {
                let result = '';
                for (let i = 0; i < data['result'].length; i++) {
                    result += `<li id="$${data['result'][i].id}" class='w3-bar-item w3-button' style='text-decoration: none; width:100%'><i class="fas fa-hashtag"></i>${data['result'][i].name}</li>`;
                }
                $('#menulist ul').html('');
                $(this).parent().children('.channels').first().html(result);
            }
        });
    });