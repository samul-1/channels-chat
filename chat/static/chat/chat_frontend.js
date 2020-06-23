const chatSocket = new WebSocket("ws://" + window.location.host + "/ws/chat/")
let expected_closure = 0
chatSocket.onopen = function () {
    console.log("Connected to chat socket");
    chatSocket.send(JSON.stringify({
        "command": "join",
        "room": '1'
    }))
}

chatSocket.onclose = function(e) {
    if(!expected_closure) {
        document.querySelector("#chat_container").innerHTML +=
            "<span class='msg err'>Server stopped responding</span>"
        document.querySelector("#chat_container").scrollTop = document.querySelector(
            "#chat_container"
        ).scrollHeight
    }
}

// renders new message and appends it to the chat container div
show_new_message = function (data) {
    if (data.username == this_user) 
        msg_class = "your_msg"
    else 
        msg_class = "others_msg"
    document.querySelector("#chat_container").innerHTML +=
        "<span class='msg " +
        msg_class +
        "'>" +
        data.username +
        ": " +
        data.message +
        "<i class='timestamp'>" +
        data.timestamp +
        "</i></span>"
    
    document.querySelector("#chat_container").scrollTop = document.querySelector(
        "#chat_container"
    ).scrollHeight
}

show_kick_message = function (data) {
    document.getElementById(data["kicked_user"]).outerHTML = ""
    if(data["kicked_user"] == this_user) {
        msg = "You were kicked from the chat"
        expected_closure = 1
    } else {
        msg =
            data["who_kicked"] +
            " kicked " +
            data["kicked_user"]
    }
     
    document.querySelector("#chat_container").innerHTML +=
        "<span class='msg err'>" +
        msg +
        "</span>"
    
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
            " <button onclick=\"kickUser('" +
            data.username +
            "')\">Kick</button></p>"
}		

chatSocket.onmessage = function (e) {
    const data = JSON.parse(e.data)
    console.log(e)
    switch(data.msg_type) {
        case 0:
            show_new_message(data)
            break
        case 2:
            show_kick_message(data)
            break
        case 4:
            show_user_joined_or_left(data, "joined")
            break
        case 5:
            show_user_joined_or_left(data, "left")
            break
        default:
            console.log("Unsupported message")
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
            'command': 'send',
            'room': '1',
            'message': message,
        })
        )
        messageInputDom.value = ""
    }
}

//document.querySelector("#kick").onclick = function (e) {
kickUser = function(toKick) {
        chatSocket.send(
        JSON.stringify({
            'command': 'kick',
            'room': '1',
            'who_kicked': this_user,
            'kicked_user': toKick,
        })
        )
}