// set to 1 when the user is kicked (or possibly is expected to disconnect for some other reason)
let expected_closure = 0

let currentRoom = '1'
const main_chatroom_id = '1'

chatSocket.onclose = function (e) {
  if (!expected_closure) {
    document.querySelector('#chat_container').innerHTML +=
      "<span class='msg err'>" +
      lang[currLang]["warning_server_stopped_responding"] +
      "</span>"
    document.querySelector(
      '#chat_container'
    ).scrollTop = document.querySelector('#chat_container').scrollHeight
  }
}

chatSocket.onmessage = function (e) {
  const data = JSON.parse(e.data)
  console.log(e)
  switch (data.msg_type) {
    case 0: // chat message
      show_new_message(data)
      break
    case 2: // kick
      show_kick_message(data)
      break
    case 3: // new private message
      create_new_private_conversation(data)
      break
    case 4: // user joined
      show_user_joined_or_left(data, 'joined')
      break
    case 5: // user left
      show_user_joined_or_left(data, 'left')
      break
    case 6: // attachment
      show_attachment(data)
      break
    case 7: // mute
      show_muted_alert(data)
      break
    default:
      console.log('Unsupported message')
      break
  }
}

// focus message input on page load
document.querySelector('#message-input').focus()
document.querySelector('#message-input').onkeyup = function (e) {
  if (e.keyCode === 13) {
    // enter, return
    document.querySelector('#submit-button').click()
  }
}
document.querySelector('#submit-button').onclick = function (e) {
  const messageInputDom = document.querySelector('#message-input')
  let whitespace = new RegExp('^\\s*$')

  if (!whitespace.test(messageInputDom.value)) { // test if the text input only contains whitespace
    const message = messageInputDom.value
    chatSocket.send(
      JSON.stringify({
        command: 'send',
        room: currentRoom,
        message: message,
      })
    )
    messageInputDom.value = '' // empty message input
  }
}

// functions that send a message to the server ------------------------------------------------------

// sends message to the server to kick a user
kickUser = function (toKick) {
  chatSocket.send(
    JSON.stringify({
      command: 'kick',
      room: '1',
      who_kicked: this_user,
      kicked_user: toKick,
      ban: '0',
    })
  )
}

toggleMuteUser = function (targetUser) {
  chatSocket.send(
    JSON.stringify({
      command: 'toggle_mute',
      room: '1',
      target: targetUser,
    })
  )
  toggleDialog(targetUser)
}

toggleSoundNotification = function () {
  chatSocket.send(
    JSON.stringify({
      command: 'toggle_sound_notification'
    })
  )
  sound_notifications_enabled = !sound_notifications_enabled
}

// sends message to the server to ban a user
banUser = function (toKick) {
    chatSocket.send(
      JSON.stringify({
        command: 'kick',
        room: '1',
        who_kicked: this_user,
        kicked_user: toKick,
        ban: '1',
      })
    )
}

// sends message to the server to create a new private conversation
newRoom = function (recipient) {
  chatSocket.send(
    JSON.stringify({
      command: 'new_private_msg',
      message: 'test',
      recipient: recipient,
    })
  )
}

// sends a private message to a user (if it's the first one, the server will create a new room)
sendPrivateMessage = function (button_id, toUser) {
  const messageInputDom = document.getElementById('msg_input_' + toUser)
  let whitespace = new RegExp('^\\s*$')

  if (!whitespace.test(messageInputDom.value)) { // test if message only contains whitespace
    const message = messageInputDom.value
    chatSocket.send(
      JSON.stringify({
        command: 'new_private_msg',
        message: message,
        recipient: toUser,
      })
    )
    messageInputDom.value = '' // empty input
    toggleDialog(toUser) // hide message popover
  }
}

// makes invisible user visible and notifies other users of their entrance
become_visible = function() {
  chatSocket.send(
      JSON.stringify({
        command: 'join',
        room: '1',
        invisible: '-1',
      })
    )
  document.getElementById("become_visible_but").outerHTML = ""
  document.getElementById("chatroom_title").style = ""
  document.getElementById("invisible_warning").outerHTML = ""
  document.getElementById("invisible_text").outerHTML = ""
  document.getElementById(this_user).classList.remove("text-muted")
  document.getElementById(this_user).classList.remove("semi-transparent")

  now = new Date()
  document.getElementById(main_chatroom_id).innerHTML +=
    "<span class='msg your_msg'>&nbsp;&rarr; " + 
    this_user +
    ' ' +
    lang[currLang]["chat_joined"] +
    ' ' +
    '<i class="timestamp">' +
    ("0" + now.getHours()).slice(-2) + 
    ':' + 
    ("0" + now.getMinutes()).slice(-2) +
    '</i></span>'

  // scroll to bottom of chat container div
  document.querySelector('#chat_container').scrollTop = document.querySelector(
    '#chat_container'
  ).scrollHeight
}

// ---------------------------------------------------------------------------------------------------


// functions that render html to the page ------------------------------------------------------------

// handles the html needed to display a new room
create_new_private_conversation = function (data) {
  const convo_list = document.getElementById('convo_list')
  const chat_container = document.getElementById('chat_container')
  const new_li = document.createElement('li')
  const new_div = document.createElement('div')

  new_li.classList.add('tab-nav-link')
  new_li.dataset.target = '#' + data.room
  new_li.id = 'nav_' + data.room
  if (this_user == data.recipient) new_li.innerHTML = data.username
  else new_li.innerHTML = data.recipient
  convo_list.appendChild(new_li)

  new_div.classList.add('chatroom')
  new_div.id = data.room
  chat_container.appendChild(new_div)

  bind_tab_selectors()
  new_li.click()
}

// displays a message containing an attachment uploaded by a user
show_attachment = function (data) {
  if (data.username == this_user) msg_class = 'your_msg'
  else msg_class = 'others_msg'

  room_id = data.room
  document.getElementById(room_id).innerHTML +=
    "<span class='msg " +
    msg_class +
    "'>" +
    data.username +
    ': <i class="fas fa-paperclip"></i> <a href="http://127.0.0.1:8000/uploads/' +
    data.url +
    "\" target='_blank'>" +
    data.url +
    "</a> - <span class='text-muted'>" +
    lang[currLang]["attachments_size"] +
    ": </span> " +
    render_filesize(data.size) +
    " <i class='timestamp'>" +
    data.timestamp +
    '</i></span>'

  if (!document.getElementById(room_id).classList.contains('curr_tab'))
    document.getElementById('nav_' + room_id).classList.add('unread_msgs')

  document.querySelector('#chat_container').scrollTop = document.querySelector(
    '#chat_container'
  ).scrollHeight
}

// handles a user joining or leaving by adding/removing relevant html and calls function to display "joined/left" message to users
show_user_joined_or_left = function (data, action) {
  // display user joined message
  if(action == "joined" && document.getElementById(data.username) !== null) // if this happens, then the user is already online but connecting from a second tab or device: don't trigger entrance events again
    return
  notify_exit_or_entrance(data, action)
  if (action == 'joined') { // && data.username != this_user
    let kick_button_html = ''
    if (this_user_is_op) {
      kick_button_html = '<button class="btn btn-sm msg-btn popup op-panel" id="' +
      data.username + 
      '_op_panel" data-html="true" data-toggle="popover" data-placement="bottom" data-content="<button style=&apos;margin-bottom: 5px&apos; class=&apos;btn btn-sm kick-btn btn-danger&apos; id=&apos;' +
      data.username +
      '_kick_btn&apos; onclick=&quot;kickUser(\'' +
      data.username +
      '\')&quot;><i class=&apos;fas fa-user-minus&apos;></i></button> <label for=&apos;' + 
      data.username + 
      '_kick_btn&apos;><span class=&apos;op_text&apos;>' +
      lang[currLang]["action_kick_user"] +
      '</span></label><br /><button style=&apos;margin-bottom: 5px&apos; class=&apos;btn btn-sm kick-btn btn-danger&apos; data-toggle=&apos;modal&apos; id=&apos;' +
      data.username + 
      '_ban_btn&apos; data-target=&apos;#banModal&apos; onclick=\'ban_target =`' +
      data.username +
      '`\'><i class=\'fas fa-user-times\'></i></button> <label for=&apos;' + 
      data.username + 
      '_ban_btn&apos;><span class=&apos;op_text&apos;>' +
      lang[currLang]["action_ban_user"] +
      '</span></label><br /><button class=&apos;btn btn-sm kick-btn btn-danger&apos; onclick=&quot;toggleMuteUser(\'' +
      data.username +
      '\')&quot; id=&quot;' +
      data.username +
      '_mute_btn&quot;><i class=\'fas fa-ban\'></i></button> <label for=&apos;' +
      data.username + 
      '_mute_btn&apos;><span id=&apos;' +
      data.username +
      '_mute_txt&apos; class=&apos;op_text&apos;>' +
      lang[currLang]["action_mute_user"] +
      '</span></label>"><i class=\'fas fa-chevron-down\'></i></button>'
        // " <button class='btn btn-sm kick-btn btn-danger' onclick=\"kickUser('" +
        // data.username +
        // "')\"><i class='fas fa-user-minus'></i></button> <button class='btn btn-sm kick-btn btn-danger' data-toggle='modal' data-target='#banModal' onclick='ban_target = \"" +
        // data.username +
        // "\"'><i class='fas fa-user-times'></i></button>"
    }
    // add username to online users list
    document.querySelector('#online_users').innerHTML +=
      "<p class='online_user' id='" +
      data.username +
      "'>&nbsp;" +
      data.username +
      kick_button_html +
      " <button class='btn btn-sm msg-btn btn-primary priv_msg_but popup' id='" +
      data.username +
      "_dialog' data-html='true' data-toggle='popover' data-placement='bottom' title='" +
      lang[currLang]["ui_send_message_to"] +
      " " +
      data.username +
      "' data-content='<div><center><textarea style=\"width: 12rem\" id=\"msg_input_" +
      data.username +
      "\"></textarea><br /><button class=\"btn btn-primary\" id=\"msg_" +
      data.username +
      "\" onclick=\"sendPrivateMessage(this.id, &apos;" +
      data.username +
      "&apos;)\">" +
      lang[currLang]["action_send"] +
      "</button></center></div>'><i class='fas fa-envelope'></i></button>"

      initializePopovers()
  }
}

render_filesize = function (size) {
  // size is given in bytes
  // returns size in megabytes if size is at least 1 MB, otherwise returns size in KB

  if(size >= 1000000)
    return Math.round((size / 1000000 + Number.EPSILON) * 100) / 100  + " MB"
  
    return Math.round((size / 1000 + Number.EPSILON) * 100) / 100 + " KB"
}

// renders new message and appends it to the chat container div
show_new_message = function (data) {
  // escape, add <a> tag to links, highlight @ mentions, and format message
  data.message = escape_HTML(data.message)
  data.message = urlify(data.message)
  data.message = format(data.message)

  mention = data.message.indexOf("@" + this_user)
  if(mention != -1) { // does the message contain "@myusername" mention?
    // does the mention contain *exactly* my username? (if my username is "sam", I don't wanna be notified when somebody types "@samuele")
    if(typeof(data.message)[mention + this_user.length + 1] == "undefined" || [',',';',':',' ', '.', '!', '?'].includes(data.message[mention + this_user.length + 1])) {
      data.message = data.message.replace('@' + this_user, "<span class='mention'>@" + this_user + "</span>")
      // send notification if enabled
      if(sound_notifications_enabled) {
        console.log(sound_notifications_enabled)
        notification_sound.play()
      }
    }
  }

  if (data.username == this_user) msg_class = 'your_msg'
  else msg_class = 'others_msg'

  let em_opening = em_enclosing = ''
  let colon = ':'

  let whitespace = new RegExp('^\\s*$') // used for testing content of "/me" messages
  // handle "/me" messages
  if(data.message.slice(0, 3) == '/me' && data.message.length > 3 && !whitespace.test(data.message.slice(3))) {
    em_opening = "<em>"
    em_enclosing = "</em>"
    colon = ""
    data.message = data.message.slice(3)
  }

  room_id = data.room
  document.getElementById(room_id).innerHTML +=
    "<span class='msg " +
    msg_class +
    "'>" +
    em_opening +
    data.username +
    colon +
    ' ' +
    data.message +
    em_enclosing +
    "<i class='timestamp'>" +
    data.timestamp +
    '</i></span>'

  if(document.getElementById('nav_' + room_id).classList.contains("hidden-link")) { // show room if it was hidden
    document.getElementById('nav_' + room_id).classList.remove("hidden-link")
    document.getElementById('nav_' + room_id).click()
  }

  if (!document.getElementById(room_id).classList.contains('curr_tab')) // if message is sent to a room different than the one is currently open, show notification next to room name
    document.getElementById('nav_' + room_id).classList.add('unread_msgs')

  // scroll to the bottom of the chat div
  document.querySelector('#chat_container').scrollTop = document.querySelector(
    '#chat_container'
  ).scrollHeight
}

// shows "you were kicked" message to kicked user and "user1 kicked user2" to everyone else
show_kick_message = function (data) {
  toggleDialog(data.kicked_user)
  document.getElementById(data['kicked_user']).outerHTML = ''
  if (data['kicked_user'] == this_user) {
    msg = lang[currLang]["warning_you_were_kicked"]
    // show "you were kicked" message in the room that's currently showing to kicked user
    tab_to_show_msg = currentRoom
    expected_closure = 1
  } else {
    msg = data['who_kicked'] +
    ' ' +
    lang[currLang]["chat_kicked"] + 
    ' ' + 
    data['kicked_user'] + 
    ' <i class="err timestamp">' +
    data.timestamp +
    '</i>'
    tab_to_show_msg = main_chatroom_id
  }

  document.getElementById(tab_to_show_msg).innerHTML +=
    "<span class='msg err'>" + msg + '</span>'

  document.querySelector('#chat_container').scrollTop = document.querySelector(
    '#chat_container'
  ).scrollHeight
}

// shows "user left/joined" message
notify_exit_or_entrance = function (data, action) {
  if(data.room != "1")
    return // only do something when users join/leave the main chat (server will send entrance/leaving messages for all private conversations as well as they are considered separate rooms, so this line prevents the function from being run multiple times per event)

  let arr

  // hide "send private message" box if it was showing when the user left
  if (action == 'left') {
    toggleDialog(data.username)

    document.getElementById(data.username).outerHTML = ''
    arr = '&larr;'
  } else {
    arr = '&rarr;'
  }
  let msg_class
  if (data.username == this_user) {
    msg_class = 'your_msg'
  } else {
    msg_class = 'others_msg'
  }

  document.getElementById(main_chatroom_id).innerHTML +=
    "<span class='msg " +
    msg_class +
    "'>&nbsp;" +
    arr +
    ' ' +
    data.username +
    ' ' +
    lang[currLang]["chat_" + action] +
    ' ' +
    "<i class='timestamp'>" +
    data.timestamp +
    '</i></span>'

  // scroll to bottom of chat container div
  document.querySelector('#chat_container').scrollTop = document.querySelector(
    '#chat_container'
  ).scrollHeight
}

show_muted_alert = function (data) {
  // if(this_user_is_op) {
  //   mute_txt = document.getElementById(data.target + "_mute_txt")
  //   if(data.new_status) {
  //     mute_txt.innerHTML = lang[currLang]["action_unmute_user"]
  //   } else {
  //     mute_txt.innerHTML = lang[currLang]["action_mute_user"]
  //   }
  // }
  document.getElementById(data.target).classList.toggle("muted")
  if(data.target == this_user) {
    muted = !muted
    const muted_msg = document.getElementById("muted_msg")
    if(muted)
      muted_msg.innerHTML = lang[currLang]["alert_you_were_muted"]
    else
      muted_msg.innerHTML = lang[currLang]["alert_you_were_unmuted"]
    
    $('#muted_alert').toast("show")
  }
}

// -----------------------------------------------------------------------------------

// utility functions -----------------------------------------------------------------

// escape html inside a message
function escape_HTML(html_str) {
  'use strict';

  return html_str.replace(/[&<>"]/g, function (tag) {
    var chars_to_replace = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
        };

    return chars_to_replace[tag] || tag;
  });
}

// detects urls inside a string and renders <a> tag
function urlify(text) {
  var urlRegex = /(https?:\/\/[^\s]+)/g;
  return text.replace(urlRegex, function(url) {
    return '<a href="' + url + '" target="_blank">' + url + '</a>';
  })
  // or alternatively
  // return text.replace(urlRegex, '<a href="$1">$1</a>')
}

// converts ** to bold and * to italic
function format(text) {
  text = text.replace(/\*\*(\S(.*?\S)?)\*\*/gm, '<strong>$1</strong>')
  return text.replace(/\*(\S(.*?\S)?)\*/gm, '<em>$1</em>')
}