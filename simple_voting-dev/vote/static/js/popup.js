let saveScreenTop = 0;
$(window).on('hashchange', () => {
    if (document.location.hash.includes("popup")) {
        $("body").css("overflow", "hidden");
        saveScreenTop = $(document).scrollTop();
    } else {
        $("body").css("overflow", "auto");
        $(document).scrollTop(saveScreenTop);
    }
});

$(document).ready(() => {
    window.location.hash = "";
});