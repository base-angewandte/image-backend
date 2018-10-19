$(document).ready(function() {
    var selectedThumbnail = null;
    var thumnailbrowserScrollPosition = $(window).scrollTop();
    const thumbnailClassName = 'show-thumbnailbrowser';
    const editClassName = 'show-edit-overlay';
    const detailClassName = 'show-detail-overlay';
    const collectClassName = 'show-collect-overlay';


    // load artwork data (JSON) and show it in the inspector/sidebar
    updateInspector = function(elInspector, artworkId) {
        $.getJSON('/artwork/'+artworkId+'.json', function(data) {
            var items = [];
            const collectButton = `<button name="add" class="collect inspector-button" onClick="showCollectOverlay(${artworkId})">Merken</button>`;
            items.push(collectButton);
            const editButton = `<button name="edit" class="edit_artwork inspector-button" onClick="showEditOverlay(${artworkId})">Edit</button>`;
            items.push(editButton);
            items.push('<dl class="artwork-details">');
            $.each( data, function( key, val ) {
                if (key === "artists") {
                    var artists = "";
                    for (var i = 0; i < val.length; i++) { 
                        artists = artists + val[i].name;
                    }
                    val = artists;
                }
                if ((val !== "") && (val !== null)) {
                    items.push(`<dt class="key-${key}">${key}</dt><dd>${val}</dd>`);
                }
            });
            items.push('</dl>');
            elInspector.html(items.join(''));
           });
    }


    // the page consists of a sidebar and a main view
    // per default, clickable thumbnails are shown
    $('.thumbnail').on('click', function (e) {
        const selectClass = 'selected';
        var clickedThumbnail = e.currentTarget;
        if ($(clickedThumbnail).hasClass(selectClass)) {
            // Clicking a thumbnail twice, shows the detail overlay
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


    // open the detail overlay
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

    // open the detail edit overlay 
    showEditOverlay = function(artworkId) {
        const url = '/artwork/' + artworkId + '/edit_overlay.html';
        // TODO: check if detail overlay open; if not remember scrollPosition
        showOverlay(editClassName);
        $('#edit-overlay').load(url, function() {
            $('.image-big').addClass('shown');
        });
    }

    // open the collect artwork overlay 
    showCollectOverlay = function(artworkId) {
        const userID = 1; // TODO: get userID!
        const url = '/artwork/' + artworkId + '/collect_overlay.html';
        // TODO: check if detail overlay open; if not remember scrollPosition
        showOverlay(collectClassName);
        $('#collect-overlay').load(url, function() {
            elInspector = $('.detail-inspector').first();
            updateInspector(elInspector, artworkId);
        });
    }   


    // close the overlay
    function closeOverlay() {
        document.body.className = thumbnailClassName;
        $(window).scrollTop(thumnailbrowserScrollPosition);
    }


    // hide the detail overlay
    hideDetailOverlay = function() {
        $('.image-big').removeClass('shown');
        closeOverlay();
    };  


    hideEditOverlay = function() {
        // TODO: reload data
        $('.image-big').removeClass('shown');
        closeOverlay();
    };


    // hide the collect artwork overlay
    hideCollectOverlay = function() {
        closeOverlay();
    };
});