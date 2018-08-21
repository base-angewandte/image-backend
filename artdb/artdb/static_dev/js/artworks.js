// functions available to other scripts:
var updateInspector;
var hideOverlay;
var state;

function loadUrl(url) {
    window.location.href = url;
    return false;
}

$(document).ready(function() {
    var selectedThumbnail = null;
    var thumnailbrowserScrollPosition = $(window).scrollTop();

    // load artwork data (JSON) and show it in the inspector
    updateInspector = function(artworkId) {
        $.getJSON('artwork/'+artworkId+'.json', function( data) {
            var items = [];
            items.push('<button name="edit" id="editartwork" class="inspector-button")>Edit</button>');
            items.push('<dl class="artwork-details">');
            // TODO: do not use html here
            // for security reasons we construct it
            $.each( data, function( key, val ) {
                if (key === "artists") {
                    var artists = "";
                    for (var i = 0; i < val.length; i++) { 
                        artists = artists + val[i].name;
                    }
                    val = artists;
                }
                if ((val !== "") && (val !== null)) {
                    items.push('<dt>' + key + '</dt> <dd>' + val + '</dd>');
                }
            });
            items.push('</dl>');
            $('#inspector').html(items.join(''));
            $('#editartwork').on('click', function (e) {
                showEditOverlay(artworkId);
                // window.location.href = url;
            });
        });
    }

    // the page consists of a sidebar and a main view
    // per default, the main view shows thumbnails
    $('.thumbnail').on('click', function (e) {
        const selectClass = 'selected';
        var clickedThumbnail = e.currentTarget;
        if ($(clickedThumbnail).hasClass(selectClass)) {
            // Clicking it twice, shows the overlay and loads its content.
            showViewOverlay(clickedThumbnail.dataset.artworkid);
        } else {
            // Clicking a thumbnail once, selects it and shows the details
            // in the inspector.
            if (selectedThumbnail !== null) {
                $(selectedThumbnail).removeClass(selectClass);
            }
            selectedThumbnail = clickedThumbnail;
            $(selectedThumbnail).addClass(selectClass);
            updateInspector(selectedThumbnail.dataset.artworkid);
        }
    });

    // show the image of a selected artwork in an overlay
    function showViewOverlay(artworkId) {
        const body = $('body');
        const shownClass = 'shown';
        const url = 'artwork/' + artworkId + '_overlay.html';
        thumnailbrowserScrollPosition = $(window).scrollTop();
        body.addClass('show-view-overlay');
        $('.image-big').removeClass(shownClass);
        $('#view-overlay').load(url, function() {
            $('.image-big').addClass(shownClass);
        });
        body.removeClass('show-thumbnailbrowser');
        $(window).scrollTop(thumnailbrowserScrollPosition);
    }

    // hide the overlay
    hideViewOverlay = function() {
        const body = $('body');
        body.addClass('show-thumbnailbrowser');
        body.removeClass('show-view-overlay');
        $(window).scrollTop(thumnailbrowserScrollPosition);
    };


    function showEditOverlay(artworkId) {
        const body = $('body');
        const shownClass = 'shown';
        const url = 'edit/' + artworkId + '.html';
        body.addClass('show-edit-overlay');
        body.removeClass('show-view-overlay');
        body.removeClass('show-thumbnailbrowser');
        $('.image-big').removeClass(shownClass);
        $('#edit-overlay').load(url, function() {
            $('.image-big').addClass(shownClass);
        });
    }

    hideEditOverlay = function() {
        const body = $('body');
        body.addClass('show-view-overlay');
        body.removeClass('show-edit-overlay');
        // TODO update artwork data
    };
});