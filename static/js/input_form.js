var form = document.getElementById("login-form");
function handleForm(event) {
  event.preventDefault();
  var formData = new FormData(form);
  // output as an object
  var data = Object.fromEntries(formData);
  form.reset();

  location.replace(`/result?ticker=${data?.ticker}&days=${data?.days}`);
}
form.addEventListener("submit", handleForm);

function handleClick() {
  event.preventDefault();
  location.replace(`/predict`);
}
