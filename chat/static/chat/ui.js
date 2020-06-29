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

toggle_msg_dialog = function() {
    $(".priv_msg_but").click(function() {
        $(this).parent().next(".message_dialog").toggle();
    }); 
}

let curr_dialog
// When the user clicks on div, open the popup
function fadeInDialog(user) {
    const popup = document.getElementById(user + "_dialog")
    if(curr_dialog != undefined && curr_dialog != popup)
        curr_dialog.classList.remove("show")
    if(curr_dialog == popup)
        curr_dialog = undefined
    curr_dialog = popup
    popup.classList.toggle("show");
    const currShow = document.getElementsByClassName("show")
  }