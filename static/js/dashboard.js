// Auto-dismiss flash alerts after a few seconds for a cleaner dashboard feel.
document.addEventListener("DOMContentLoaded", function () {
  var alerts = document.querySelectorAll(".alert");
  alerts.forEach(function (alertEl) {
    setTimeout(function () {
      var closeBtn = alertEl.querySelector(".btn-close");
      if (closeBtn) {
        closeBtn.click();
      }
    }, 6000);
  });
});
