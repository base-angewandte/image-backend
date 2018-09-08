// functions available to other scripts:
/*function loadUrl(url) {
    window.location.href = url;
    return false;
}*/

$(document).ready(function() {
    var selectedThumbnail = null;
    var bLastStateThumbnailbrowser = false; // needed for hideEditOverlay
    var thumnailbrowserScrollPosition = $(window).scrollTop();

    // load artwork data (JSON) and show it in the inspector
    updateInspector = function(artworkId) {
        $.getJSON('/artwork/'+artworkId+'.json', function( data) {
            var items = [];
            items.push('<button name="add" id="add_to_collection" class="inspector-button")>Merken</button>');
            items.push('<button name="edit" id="edit_artwork" class="inspector-button")>Edit</button>');
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
            $('#edit_artwork').on('click', function (e) {
                showEditOverlay(artworkId);
            });
            $('#add_to_collection').on('click', function (e) {
                showEditOverlay(artworkId);
            });
        });
    }

    // the page consists of a sidebar and a main view
    // per default, the thumbnails are shown
    $('.thumbnail').on('click', function (e) {
        const selectClass = 'selected';
        var clickedThumbnail = e.currentTarget;
        if ($(clickedThumbnail).hasClass(selectClass)) {
            // Clicking it twice, shows the detail overlay
            showDetailOverlay(clickedThumbnail.dataset.artworkid);
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
    function showDetailOverlay(artworkId) {
        const body = $('body');
        const shownClass = 'shown';
        const url = '/artwork/' + artworkId + '_detail_overlay.html';
        thumnailbrowserScrollPosition = $(window).scrollTop();
        body.addClass('show-detail-overlay');
        $('.image-big').removeClass(shownClass);
        $('#detail-overlay').load(url, function() {
            $('.image-big').addClass(shownClass);
        });
        body.removeClass('show-thumbnailbrowser');
        $(window).scrollTop(thumnailbrowserScrollPosition);
    }

    // hide the overlay
    hideDetailOverlay = function() {
        const body = $('body');
        body.addClass('show-thumbnailbrowser');
        body.removeClass('show-detail-overlay');
        $(window).scrollTop(thumnailbrowserScrollPosition);
    };


    function showEditOverlay(artworkId) {
        const body = $('body');
        const shownClass = 'shown';
        const url = '/artwork/edit/' + artworkId + '.html';
        console.log(artworkId);
        bLastStateThumbnailbrowser = $('body').hasClass("show-thumbnailbrowser");
        body.addClass('show-edit-overlay');
        body.removeClass('show-detail-overlay');
        body.removeClass('show-thumbnailbrowser');
        $('.image-big').removeClass(shownClass);
        $('#edit-overlay').load(url, function() {
            $('.image-big').addClass(shownClass);
        });
    }

    hideEditOverlay = function() {
        const body = $('body');
        // TODO: reload data!
        if (bLastStateThumbnailbrowser) {
            body.addClass('show-thumbnailbrowser');          
        } else {
            body.addClass('show-detail-overlay');
        }
        body.removeClass('show-edit-overlay');
    };
});