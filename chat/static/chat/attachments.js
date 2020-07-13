// function upload(event) {
//     event.preventDefault()
//     var data = new FormData($('#attachment_form').get(0))
//     $.ajax({
//       url: $(this).attr('action'),
//       type: $(this).attr('method'),
//       data: data,
//       cache: false,
//       processData: false,
//       contentType: false,
//     })
//     var fullPath = document.getElementById('id_file').value
//     if (fullPath) {
//       var startIndex =
//         fullPath.indexOf('\\') >= 0
//           ? fullPath.lastIndexOf('\\')
//           : fullPath.lastIndexOf('/')
//       var filename = fullPath.substring(startIndex)
//       if (filename.indexOf('\\') === 0 || filename.indexOf('/') === 0) {
//         filename = filename.substring(1)
//       }
//       //alert(filename);
//     }
//     $('#id_file').val('')
  
//     // send message to server
//     chatSocket.send(
//       JSON.stringify({
//         command: 'attachment',
//         room: currentRoom,
//         file: filename,
//       })
//     )
//     return false
//   }
  
//   $(function () {
//     $('#attachment_form').submit(upload)
//   })
  