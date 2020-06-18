const chatSocket = new WebSocket("ws://" + window.location.host + "/ws/chat/")

show_new_message = function (data) {
    if (data.sent_by == this_user) 
        msg_class = "your_msg"
    else 
        msg_class = "others_msg"
    document.querySelector("#chat_container").innerHTML +=
        "<span class='msg " +
        msg_class +
        "'>" +
        data.sent_by +
        ": " +
        data.message +
        "<i class='timestamp'>" +
        data.timestamp +
        "</i></span>"
    
    document.querySelector("#chat_container").scrollTop = document.querySelector(
        "#chat_container"
    ).scrollHeight
}

notify_exit_or_entrance = function(data, action) {
    let arr
    if(action == "left") {
        document.getElementById(data.username).outerHTML = ""
        arr = "&larr;"
    } else {
        arr = "&rarr;"
    }
    let msg_class
    if(data.username == this_user) {
        msg_class = "your_msg"
    } else {
        msg_class = "others_msg"
    }
    document.querySelector("#chat_container").innerHTML +=
        "<span class='msg " +
        msg_class +
        "'>&nbsp;" +
        arr +
        " " +
        data.username +
        " " +
        action +
        " the chatroom" +
        "<i class='timestamp'>" +
        data.timestamp +
        "</i></span>"
    chatSocket.send(
        JSON.stringify({
            message: action,
            type: 'system'
        })
    )
    document.querySelector("#chat_container").scrollTop = document.querySelector(
        "#chat_container"
    ).scrollHeight
}

show_user_joined_or_left = function(data, action) {
    // display user joined message
    notify_exit_or_entrance(data, action)
    if(action == "joined" && data.username != this_user)
        // add username to online users list
        document.querySelector("#online_users").innerHTML +=
            "<p id='"+
            data.username +
            "'>" +
            data.username +
            "</p>"
}		

chatSocket.onmessage = function (e) {
    const data = JSON.parse(e.data)
    switch(data.message_type) {
        case "chat_message":
            show_new_message(data)
            break
        case "user_joined":
            show_user_joined_or_left(data, "joined")
            break
        case "user_left":
            show_user_joined_or_left(data, "left")
            break
    }
}

document.querySelector("#message-input").focus()
document.querySelector("#message-input").onkeyup = function (e) {
    if (e.keyCode === 13) {
        // enter, return
        document.querySelector("#submit-button").click()
    }
}
document.querySelector("#submit-button").onclick = function (e) {
    const messageInputDom = document.querySelector("#message-input")
    let whitespace = new RegExp("^\\s*$")

    if (!whitespace.test(messageInputDom.value)) {
        const message = messageInputDom.value
        chatSocket.send(
        JSON.stringify({
            type: 'user',
            message: message,
        })
        )
        messageInputDom.value = ""
    }
}