// global variables used across all javascripts
var selectedThumbnail = null;


$(document).ready(function() {
    var thumbnailbrowserScrollPosition = $(window).scrollTop();
    var elCurrentInspector = null;
    const thumbnailClassName = 'show-thumbnailbrowser';
    const editClassName = 'show-edit-overlay';
    const detailClassName = 'show-detail-overlay';
    const collectClassName = 'show-collect-overlay';
    var bSmallTopbar = false;


    // ---------------------------------------------------------
    // Get the CSRF Token
    // see: https://docs.djangoproject.com/en/2.2/ref/csrf/#ajax
    // ---------------------------------------------------------
    // var csrftoken = jQuery("[name=csrfmiddlewaretoken]").val();


    // ---------------------------------------------------------
    // Helper Function
    // creates document elements with optional css classes, text
    // and a dataset.url
    // ---------------------------------------------------------
    function createEl(tagName, cssClasses, text, url) {
        var el = document.createElement(tagName);
        cssClasses.forEach(function(cssClassName) {
            el.classList.add(cssClassName);
        });
        if (text) el.appendChild(document.createTextNode(text));
        if (url) el.dataset.url = url;
        return el;
    }


    // ---------------------------------------------------------
    // Update the Inspector
    // load artwork data (JSON) and show it in the sidebar
    // ---------------------------------------------------------
    updateInspector = function(elInspector) {
        const url = selectedThumbnail.dataset.url;
        const jsonUrl = url + '.json';
        $.getJSON(jsonUrl, function(data) {
            var elDetails = document.createElement('div');
            elDetails.appendChild(createEl('button', ['inspector-button', 'button-collect'], gettext('addtocollection'), url));
            if (elInspector.classList.contains('editable')) {
                elDetails.appendChild(createEl('button', ['inspector-button','button-edit'], gettext('Edit'), url));
            };
            if (selectedThumbnail.dataset.membershipid) {
                var leftButton = createEl('button', ['inspector-button','button-move-left'], '', url);
                leftButton.dataset.action = 'move';
                var rightButton = createEl('button', ['inspector-button','button-move-right'], '', url);
                rightButton.dataset.action = 'move';
                elDetails.appendChild(leftButton);
                elDetails.appendChild(rightButton);
            };
            // build all the elements and append them to the DOM 
            $.each( data, function( key, val ) {
                if (!val) return;
                var elKey, elVal;
                var elEntry = document.createElement('div');
                switch (key) {
                    case 'artists':
                        if (val.length === 0) break;
                        elKey = createEl('div', ['key'], gettext('Artist'));
                        elEntry.appendChild(elKey);
                        for (var i = 0; i < val.length; i++) {
                            elVal = createEl('div', ['value','tag'], val[i].name);
                            elVal.dataset.artist = val[i].name;
                            elEntry.appendChild(elVal);
                        }
                        break;
                    case 'keywords':
                        if (val.length === 0) break;
                        elKey = createEl('div', ['key'], gettext('Keywords'));
                        elEntry.appendChild(elKey);
                        for (var i = 0; i < val.length; i++) {
                            elVal = createEl('div', ['value','tag'], val[i].name);
                            elVal.dataset.keyword = val[i].name;
                            elEntry.appendChild(elVal);
                        }
                        break;
                    case 'location_of_creation':
                        if (val.length === 0) break;
                        elKey = createEl('div', ['key'], gettext('location_of_creation'));
                        elEntry.appendChild(elKey);
                        elVal = createEl('div', ['value','tag'], val.name);
                        elVal.dataset.location_of_creation = val.name;
                        elEntry.appendChild(elVal);
                        break;
                    case 'location_current':
                        if (val.length === 0) break;
                        elKey = createEl('div', ['key'], gettext('location_current'));
                        elEntry.appendChild(elKey);
                        elVal = createEl('div', ['value','tag'], val.name);
                        elVal.dataset.location_current = val.name;
                        elEntry.appendChild(elVal);
                        break;
                    case 'published':
                        break;
                    case 'checked':
                        break;
                    default:
                        if ((val !== '') && (val !== null)) {
                            elKey = createEl('div', ['key'], gettext(key));
                            elEntry.appendChild(elKey);
                            elVal = createEl('div', ['value'], val);
                            if (key === 'title_english') {
                                elKey.classList.add('key-titleEnglish');
                                elVal.classList.add('val-titleEnglish');
                            }
                            elEntry.appendChild(elVal);
                        }
                }
                elDetails.appendChild(elEntry);
            }); 
            elInspector.replaceChild(elDetails, elInspector.getElementsByTagName('div')[0]);
            elCurrentInspector = elInspector;
        });
    }

    // copy the content from one inspector to another
    // this avoids unnecessary reloads
    function copyInspectorDetails(elNewInspector) {
        if (elCurrentInspector) {
            elCurrentDetails = elCurrentInspector.getElementsByTagName('div')[0].cloneNode(true);
            elNewInspector.replaceChild(elCurrentDetails, elNewInspector.getElementsByTagName('div')[0]);
            elCurrentInspector = elNewInspector;
        }
    }

    // hide the detail or edit overlay
    hideImageAndOverlay = function() {
        $('.image-big').removeClass('shown');
        closeOverlay();
    };  

    // hide the overlay
    closeOverlay = function() {
        var elNewInspector = document.getElementById('thumbnailbrowser-inspector');
        if (elNewInspector) {
            copyInspectorDetails(elNewInspector);
        }
        document.body.className = thumbnailClassName;
        window.scrollTo(0,thumbnailbrowserScrollPosition);
    }

    // show a specific overlay
    function showOverlay(classNameToAdd) {
        if ($('body').hasClass(thumbnailClassName)) {
            // no overlay is currently shown
            // remember the scroll position
            thumbnailbrowserScrollPosition = $(window).scrollTop();
            document.body.className = classNameToAdd;
            window.scrollTo(0, 0);
        } else {
            // an overlay is already shown
            // close the current overlay before showing the new one
            // (detail -> collect, detail -> edit, collect -> edit)
            document.body.className = classNameToAdd;
        }
    }

    // show the detail overlay
    function showDetailOverlay(url) {
        var overlayUrl = url + '/detail_overlay/';
        $('#detail-overlay').load(overlayUrl, function() {
            var elInspector = document.getElementById('detail-overlay-inspector');
            copyInspectorDetails(elInspector);
            $('.image-big').addClass('shown');
            showOverlay(detailClassName);
        });
    }

    // show the collect artwork overlay 
    showCollectOverlay = function(url) {
        var overlayUrl = url + '/collect_overlay/';
        $('#collect-overlay').load(overlayUrl, function() {
            elInspector = document.getElementById('collect-overlay-inspector');
            copyInspectorDetails(elInspector);
            showOverlay(collectClassName);
        });
    }

    updateCollectOverlay = function(url) {
        $('#collect-overlay').load(url, function() {
            elInspector = document.getElementById('collect-overlay-inspector');
            copyInspectorDetails(elInspector);
        });
    }

    // show the detail edit overlay
    showEditOverlay = function(url) {
        var overlayUrl = url + '/edit_overlay/';
        elNewInspector = null;
        $('#edit-overlay').load(overlayUrl, function() {
            $('.image-big').addClass('shown');
            showOverlay(editClassName);
        });
    }

    showCollectionEditOverlay = function(url) {
        $('#edit-overlay').load(url, function() {
            showOverlay(editClassName);
        });
    }

    // do not submit empty form fields
    $("#search-expert").submit(function() {
        $(this).find(":input").filter(function() { return !this.value; }).attr("disabled", "disabled");
        return true;
    });
    $("form" ).find(":input").prop("disabled", false);

    showExpertSearch = function(bAnimated) {
        if (bAnimated) {
            $('#search-basic').addClass('fadeout')
            .one('transitionend', function() {
                $('#search-basic').addClass('hidden');
            });
            $('#search-expert').removeClass('hidden');
            $('#search-expert-fold').addClass('unfolded')
            .one('transitionend', function() {
                $('#search-expert').removeClass('fadeout');
            });
        } else {
            $('#search-basic').addClass('hidden', 'fadeout');
            $('#search-expert').removeClass('hidden');
            $('#search-expert').removeClass('fadeout');         
            $('#search-expert-fold').addClass('unfolded-noanimation');
        }
    }

    showBasicSearch = function() {
        $('#search-basic').removeClass('hidden');
        $('#search-expert').addClass('fadeout');
        if ($('#search-expert-fold').hasClass('unfolded-noanimation')) {
            $('#search-expert-fold').addClass('unfolded');
            $('#search-expert-fold').removeClass('unfolded-noanimation');
        }
        $('#search-expert-fold').removeClass('unfolded')
        .one('transitionend', function() {
            $('#search-basic').removeClass('fadeout'); 
        });
    }

    // search basic/expert switch
    $("#js-search-switch").click(function(e) {
        if ($(this).prop('checked')) {
            showExpertSearch(true);
        } else {
            showBasicSearch();
        }
    });
    
    // ---------------------------------------------------
    // event listeners
    // ---------------------------------------------------

    window.addEventListener('scroll', throttle(handleScroll, 30));

    // the page consists of a sidebar and a main view
    // per default, clickable thumbnails are shown
    $('.thumbnail-area').on('click', '.thumbnail', function (e) {
        const selectClass = 'selected';
        var clickedThumbnail = e.currentTarget;
        if ($(clickedThumbnail).hasClass(selectClass)) {
            // Clicking a thumbnail twice, shows the detail overlay
            showDetailOverlay(clickedThumbnail.dataset.url);
        } else {
            // Clicking a thumbnail once, selects it and shows the details
            // in the inspector.
            if (selectedThumbnail !== null) {
                $(selectedThumbnail).removeClass(selectClass);
            }
            selectedThumbnail = clickedThumbnail;
            $(selectedThumbnail).addClass(selectClass);
            elInspector = document.getElementById('thumbnailbrowser-inspector');
            updateInspector(elInspector);
        }
    });

    $('.clear-search-artwork-field').on('click', function(e) {
        $(this).hide();
        $('#search-basic-artworks-field').focus();
    });

    $('#search-basic-artworks-field').keyup(function() {
        if ($(this).val()) {
            $('.clear-search-artwork-field').show();
        } else {
            $('.clear-search-artwork-field').hide();
        }
    });

    $("body").on('click', function (e) {
        if (e.target.classList.contains('thumbnail')) {
            const selectClass = 'selected';
            var clickedThumbnail = e.currentTarget;
            if ($(clickedThumbnail).hasClass(selectClass)) {
                // Clicking a thumbnail twice, shows the detail overlay
                showDetailOverlay(clickedThumbnail.dataset.url);
            } else {
                // Clicking a thumbnail once, selects it and shows the details
                // in the inspector.
                if (selectedThumbnail !== null) {
                    $(selectedThumbnail).removeClass(selectClass);
                }
                selectedThumbnail = clickedThumbnail;
                $(selectedThumbnail).addClass(selectClass);
                elInspector = document.getElementById('thumbnailbrowser-inspector');
                updateInspector(elInspector);
            }
        } else if (e.target.classList.contains('tag')) {
            function getParameters(s) {
                return s.replace(/\s/g, "+");
            }
            var url = "?searchtype=expert&";
    
            if (e.target.dataset.artist) {
                var artist = encodeURIComponent(e.target.dataset.artist.trim());
                url += `artist=${artist}`;
            }
            if (e.target.dataset.keyword) {
                var keyword = encodeURIComponent(e.target.dataset.keyword.trim());
                url += `keyword=${keyword}`;
            }
            if (e.target.dataset.location_of_creation) {
                var location_of_creation = encodeURIComponent(e.target.dataset.location_of_creation.trim());
                url += `location_of_creation=${location_of_creation}`;
            }
            if (e.target.dataset.location_current) {
                var location_current = encodeURIComponent(e.target.dataset.location_current.trim());
                url += `location_current=${location_current}`;
            }
            window.location.href = url;
        } else if ($(e.target).hasClass('button-collect')) {
            showCollectOverlay(e.target.dataset.url);
        } else if ($(e.target).hasClass('button-edit')) {
            showEditOverlay(e.target.dataset.url);
        } else if ($(e.target).hasClass('button-move-left')) {
            moveArtwork(selectedThumbnail, 'left');
        } else if ($(e.target).hasClass('button-move-right')) {
            moveArtwork(selectedThumbnail, 'right');
        }
    });


    // ---------------------------------------------------
    // Base layout scroll handling
    // ---------------------------------------------------

    function handleScroll() {
        if (window.pageYOffset >= 32) {
            $('#topbar').addClass('small');
            $('.button-close').addClass('fixed');
            bSmallTopbar = true;
        } else {
            if (bSmallTopbar) {
                $('#topbar').removeClass('small');
                $('.button-close').removeClass('fixed');
                bSmallTopbar = false;
            }
        }
    }

    function throttle(callback) {
        var active = false; // a simple flag
        var evt; // to keep track of the last event
        var handler = function(){ // fired only when screen has refreshed
          active = false; // release our flag 
          callback(evt);
        }
        return function handleEvent(e) { // the actual event handler
          evt = e; // save our event at each call
          if (!active) { // only if we weren't already doing it
            active = true; // raise the flag
            requestAnimationFrame(handler); // wait for next screen refresh
          };
        }
    }
});