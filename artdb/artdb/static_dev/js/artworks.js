// functions available to other scripts:
/*function loadUrl(url) {
    window.location.href = url;
    return false;
}*/

$(document).ready(function() {
    var selectedThumbnail = null;
    var thumnailbrowserScrollPosition = $(window).scrollTop();
    const thumbnailClassName = 'show-thumbnailbrowser';
    const editClassName = 'show-edit-overlay';
    const detailClassName = 'show-detail-overlay';
    const collectionsClassName = 'show-collections-overlay';
    const collectClassName = 'show-collect-overlay';

    // load artwork data (JSON) and show it in the inspector
    updateInspector = function(elInspector, artworkId) {
        console.log("updating");
        $.getJSON('/artwork/'+artworkId+'.json', function( data) {
            var items = [];
            const collectButton = `<button name="add" class="collect inspector-button" onClick="showCollectOverlay(${artworkId})">Merken</button>`;
            items.push(collectButton);
            const editButton = `<button name="edit" class="edit_artwork inspector-button" onClick="showEditOverlay(${artworkId})">Edit</button>`;
            items.push(editButton);
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
            elInspector.html(items.join(''));
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
            elInspector = $('#thumbnailbrowser-inspector');
            updateInspector(elInspector, selectedThumbnail.dataset.artworkid);
        }
    });

    // switch to a specific view
    function showOverlay(classNameToAdd) {
        document.body.className = classNameToAdd;
    }

    // switch back to the view used before
    function closeOverlay() {
        document.body.className = thumbnailClassName;
    }

    showEditOverlay = function(artworkId) {
        const body = $('body');
        const url = '/artwork/' + artworkId + '/edit_overlay.html';
        showOverlay(editClassName);
        $('#edit-overlay').load(url, function() {
            $('.image-big').addClass('shown');
        });
    }

    hideEditOverlay = function() {
        // TODO: reload data!
        console.log("hiding edit");
        $('.image-big').removeClass('shown');
        closeOverlay();
    };

    /*function showCollectionOverlay(artworkId) {
        const userID = 1; // TODO: get userID!
        const url = '/user/' + userID + 'collections.html';
        showOverlay(collectionsClassName);
        $('#collections-overlay').load(url, function() {
            elInspector = $('.detail-inspector').first();
            updateInspector(elInspector, artworkId);
        });
    }*/

    showCollectOverlay = function(artworkId) {
        const userID = 1; // TODO: get userID!
        const url = '/artwork/' + artworkId + '/collect_overlay.html';
        showOverlay(collectClassName);
        $('#collect-overlay').load(url, function() {
            elInspector = $('.detail-inspector').first();
            updateInspector(elInspector, artworkId);
        });
    }   

    hideCollectionsOverlay = function() {
        returnToPreviousView(collectionsClassName);
    };  

    // show the image of a selected artwork in an overlay
    function showDetailOverlay(artworkId) {
        const shownClass = 'shown';
        const url = '/artwork/' + artworkId + '/detail_overlay.html';
        thumnailbrowserScrollPosition = $(window).scrollTop();
        showOverlay(detailClassName);
        $('#detail-overlay').load(url, function() {
            elInspector = $('.detail-inspector').first();
            updateInspector(elInspector, artworkId);            
            $('.image-big').addClass(shownClass);
        });
    }

    // hide the detail overlay
    // TODO REMOVE?
    hideDetailOverlay = function() {
        $('.image-big').removeClass('shown');
        closeOverlay();
        $(window).scrollTop(thumnailbrowserScrollPosition);
    };  

    // hide the overlay
    hideOverlay = function() {
        document.body.className = thumbnailClassName;
        $(window).scrollTop(thumnailbrowserScrollPosition);
    };  
});