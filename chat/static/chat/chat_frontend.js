const chatSocket = new WebSocket("ws://" + window.location.host + "/ws/chat/")
let expected_closure = 0
chatSocket.onopen = function () {
    console.log("Connected to chat socket");
    chatSocket.send(JSON.stringify({
        "command": "join",
        "room": '1'
    }))
}

let currentRoom = '1'
const main_chatroom_id = '1'

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
    
    room_id = data.room
    document.getElementById(room_id).innerHTML +=
        "<span class='msg " +
        msg_class +
        "'>" +
        data.username +
        ": " +
        data.message +
        "<i class='timestamp'>" +
        data.timestamp +
        "</i></span>"
    
    if(!document.getElementById(room_id).classList.contains("curr_tab"))
        document.getElementById("nav_" + room_id).classList.add("unread_msgs")
    
    document.querySelector("#chat_container").scrollTop = document.querySelector(
        "#chat_container"
    ).scrollHeight
}

show_kick_message = function (data) {
    document.getElementById(data["kicked_user"]).outerHTML = ""

    if(data["kicked_user"] == this_user) {
        msg = "You were kicked from the chat"
        tab_to_show_msg = currentRoom
        expected_closure = 1
    } else {
        msg =
            data["who_kicked"] +
            " kicked " +
            data["kicked_user"]
        tab_to_show_msg = main_chatroom_id
    }
     
    document.getElementById(tab_to_show_msg).innerHTML +=
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
    document.getElementById(main_chatroom_id).innerHTML +=
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
    if(action == "joined" && data.username != this_user) {
        // add username to online users list
        document.querySelector("#online_users").innerHTML +=
            "<p id='"+
            data.username +
            "'>" +
            data.username +
            " <button onclick=\"kickUser('" +
            data.username +
            "')\">Kick</button>" +
            "<button class='priv_msg_but popup' onclick='fadeInDialog(\"" +
            data.username +
            "\")'>Message</button><div class='popuptext' id='" +
            data.username +
            "_dialog'><p>Send message to " +
            data.username +
            ":</p> <textarea id='msg_input_" +
            data.username +
            "'></textarea><button id='msg_" +
            data.username +
            "' onclick='sendPrivateMessage(this.id, \"" +
            data.username +
            "\")'>Send</button></div></p>"

            toggle_msg_dialog()
    }
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
        case 3:
            create_new_private_conversation(data)
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
            'room': currentRoom,
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

newRoom = function(recipient) {
    chatSocket.send(
        JSON.stringify({
            'command': 'new_private_msg',
            'message': 'test',
            'recipient': recipient
        })
        )
}

sendPrivateMessage = function(button_id, toUser) {
    const messageInputDom = document.getElementById("msg_input_" + toUser)
    let whitespace = new RegExp("^\\s*$")
    console.log(messageInputDom.value)

    if (!whitespace.test(messageInputDom.value)) {
        const message = messageInputDom.value
        chatSocket.send(
        JSON.stringify({
            'command': 'new_private_msg',
            'message': message,
            'recipient': toUser
        })
        )
        messageInputDom.value = ""
        fadeInDialog(toUser)
    }
}

create_new_private_conversation = function(data) {
    const convo_list = document.getElementById("convo_list")
    const chat_container = document.getElementById("chat_container")
    const new_li = document.createElement('li')
    const new_div = document.createElement('div')

    new_li.classList.add("tab-nav-link")
    new_li.dataset.target = "#" + data.room
    if(this_user == data.recipient)
        new_li.innerHTML = data.username
    else
        new_li.innerHTML = data.recipient
    convo_list.appendChild(new_li)

    new_div.classList.add("chatroom")
    new_div.id = data.room
    chat_container.appendChild(new_div)

    bind_tab_selectors()
}