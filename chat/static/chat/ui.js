$(document).ready(function() {
    $(function() {
        var main_chat = $("#chat_container").find('.chatroom').first()
        main_chat.show();
        document.querySelector("#chat_container").scrollTop = document.querySelector(
            "#chat_container"
        ).scrollHeight

        bind_tab_selectors()
        $('.tab-nav-link:first-child').trigger('click');

        //toggle_msg_dialog()
    });
    $(document).on('submit', '#attachment_form', function(event){
        event.preventDefault();
        var data = new FormData($('#attachment_form').get(0))
        $.ajax({
        url: $(this).attr('action'),
        type: $(this).attr('method'),
        data: data,
        cache: false,
        processData: false,
        contentType: false,
        })
        var fullPath = document.getElementById('id_file').value
        if (fullPath) {
        var startIndex =
            fullPath.indexOf('\\') >= 0
            ? fullPath.lastIndexOf('\\')
            : fullPath.lastIndexOf('/')
        var filename = fullPath.substring(startIndex)
        if (filename.indexOf('\\') === 0 || filename.indexOf('/') === 0) {
            filename = filename.substring(1)
        }
        //alert(filename);
        }

        // send message to server
        chatSocket.send(
        JSON.stringify({
            command: 'attachment',
            room: currentRoom,
            //file: filename,
        })
        )
        return false
    });
});

bind_tab_selectors = function() {
    $('.tab-nav-link').bind('click', function(e) {
        $this = $(this);
        $tabs = $this.parent().parent().next();
        $target = $($this.data("target")); // get the target from data attribute
        $this.siblings().removeClass('current');
        $target.siblings().css("display", "none")
        $target.siblings().removeClass("curr_tab");
        $this.addClass('current');
        $this.removeClass('unread_msgs');
        $target.fadeIn("fast");
        $target.addClass("curr_tab");
        currentRoom = $this.data("target").slice(1)
        document.querySelector("#chat_container").scrollTop = document.querySelector(
            "#chat_container"
        ).scrollHeight
    });
}

let curr_dialog