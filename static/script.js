var form = document.getElementById("login-form");
function handleForm(event) {
  console.log("hewo");
  event.preventDefault();
  var formData = new FormData(form);
  // output as an object
  var data = Object.fromEntries(formData);
  form.reset();
  location.replace(`/result?tinker=${data?.tinker}&days=${data?.days}`);
}
form.addEventListener("submit", handleForm);
