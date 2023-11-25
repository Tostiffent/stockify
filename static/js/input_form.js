let form = document.getElementById("login-form");
function handleForm(event) {
  event.preventDefault();
  let formData = new FormData(form);
  // output as an object
  let data = Object.fromEntries(formData);
  form.reset();

  // spinner
  let spinner = document.getElementById("spinner")
  spinner.classList.add("show") 

  location.replace(`/result?ticker=${data?.ticker}&days=${data?.days}`);
}
form.addEventListener("submit", handleForm);
