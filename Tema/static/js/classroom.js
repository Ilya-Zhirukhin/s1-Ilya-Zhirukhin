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