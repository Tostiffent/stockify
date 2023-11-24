var form = document.getElementById("chat_input_form");
async function handleForm(event) {
  event.preventDefault();
  var area = document.getElementById("chat_area");
  area.innerHTML = "clicked";
  var formData = new FormData(form);
  // output as an object
  var data = Object.fromEntries(formData);
  form.reset();
  const response = await fetch("http://localhost:5000/api", {
    method: "POST", // *GET, POST, PUT, DELETE, etc.
    mode: "cors", // no-cors, *cors, same-origin
    cache: "no-cache", // *default, no-cache, reload, force-cache, only-if-cached
    credentials: "same-origin", // include, *same-origin, omit
    headers: {
      "Content-Type": "application/json",
      // 'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: JSON.stringify(data),
  });

  response.json().then((data) => console.log(data));
}
form.addEventListener("submit", handleForm);
