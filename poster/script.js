(function () {
  const poster = document.querySelector(".poster");
  if (!poster) {
    return;
  }

  const params = new URLSearchParams(window.location.search);
  const mode = params.get("mode");

  if (mode === "debug" || mode === "export") {
    poster.dataset.mode = mode;
  }
})();
