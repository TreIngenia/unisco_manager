user_tables = $("#users_tables").DataTable({
    // "dom": "<'row '<'#toolbar.col-md-10 col-sm-12 mb-2'T><'#toolbar3.col-md-2 col-sm-12 text-right'B><'col-md-12 col-sm-12'<'#filters.form-row'>>r>t<'row mt-2'<'col-md-4 col-sm-12'i><'col-md-4 col-sm-12 text-center' l><'col-md-4 col-sm-12'p>>",
    //Personalizzazione colonne
    scrollX: false,  // Attiva lo scorrimento orizzontale per mostrare tutte le colonne
    autoWidth: false,  // Disabilita l'autowidth per rispettare le larghezze definite
    scrollCollapse: true,  // Migliora lo scorrimento
    // scrollY: "500px",
    // Configurazione per ottimizzare le prestazioni
    deferRender: true,
    processing: true,
    stateSave: false,
    // Resto della configurazione...
    // dom:
    //     `<"row "<"col-sm-12 col-md-4 d-flex align-items-center justify-content-center justify-content-md-start dt-toolbar"li>
    //     <"#filter_container.col-sm-12 col-md-4 mb-1 d-flex align-items-center justify-content-center dt-toolbar">
    //     <"col-sm-12 col-md-4 d-flex align-items-center justify-content-center justify-content-md-end"p>>
    //     <"row"<"col-sm-12"t>>
    //     <"row "<"col-sm-12 col-md-6 d-flex align-items-center justify-content-center justify-content-md-start dt-toolbar"li>
    //     <"col-sm-12 col-md-6 d-flex align-items-center justify-content-center justify-content-md-end"p>>`,
    dom:
        `
        <"row"
            <"#filter_container.col-12 d-flex align-items-center justify-content-start dt-toolbar mb-2 ">
        >
        <"row"<"col-sm-12"t>>
        <"row"
            <"col-sm-12 col-md-6 d-flex align-items-center justify-content-center justify-content-md-start dt-toolbar"li>
            <"col-sm-12 col-md-6 d-flex align-items-center justify-content-center justify-content-md-end"p>
        >`,
    buttons: [
          'copy', 'excel', 'pdf'
        ],
    pageLength: 25,
    lengthMenu: [[10, 25, 50, 100, -1], [10, 25, 50, 100, "Tutti"]],
    language: {
        url: "assets/js/data_tables_it_IT.json",
        paginate: {
            previous: "<i class='previous'></i>",
            next: "<i class='next'></i>",
        },
        select: {
            rows: {
                _: "%d selezionate",
                0: "",
                1: "1 selezionata"
            },
            columns: {
                _: "", //"%d colonne selezionate",
                0: "", //"Nessuna colonna selezionata",
                1: '', //"1 colonna selezionata"
            },
            cells: {
                _: '', //"%d celle selezionate",
                0: '', //"Nessuna cella selezionata",
                1: '', //"1 cella selezionata"
            }
            
        },
        search: "Cerca:",           
        lengthMenu: "_MENU_",  
        info: "da _START_ a _END_ di _TOTAL_", 
    },
    "columnDefs": [
        { width: "1%",  title: `<div class="form-check form-check-sm form-check-custom form-check-solid">
                            <input class="form-check-input checkbox_multiple"  data-kt-check-target="#users_tables .checkbox_single" type="checkbox"  />
                        </div>`, orderable: false, searchable: false, visible: true, className: "align-middle  px-3", responsivePriority: 1, targets: 0},
        { width: "25%", title: "Nome",orderable: true, searchable: true, visible: true, className: "align-middle text-start", responsivePriority: 1, targets: 1 },
        { width: "25%", title: "E-Mail", orderable: true, searchable: true, visible: true, className: "align-middle text-start", responsivePriority: 10001, targets: 2 },
        { width: "20%", title: "Mobile", orderable: true, searchable: true, visible: true, className: "align-middle text-start", responsivePriority: 10001, targets: 3 },
        { width: "28%",title: "TEST", orderable: true, searchable: true, visible: true, className: "align-middle text-start", responsivePriority: 1, targets: 4 },
        { width: "1%", title: "",orderable: false, searchable: false, visible: true, className: "align-middle px-2", responsivePriority: 1, targets: 5 },
    ],
    //Ordine Colonne
    "columns": [
        {   
            "data": "uid", 
            "render": function ( data, type, row, index ) {
                return `<div class="form-check form-check-sm form-check-custom form-check-solid">
                            <input class="form-check-input checkbox_single" type="checkbox" value="${data}" />
                        </div>`
                        
            }
        },
        {   
            "data": "name_surname", 
            "render": function ( data, type, row ) {
                var x = row['active'];
                var y = row['main_company']
                var status = row['status']
                
                if(status == 'ONLINE'){
                    var online='<div class="badge mr-1 help" data-bs-toggle="tooltip" data-placement="top" title="ONLINE"><i class="fa fa-circle text-success"></i></div>';
                }else{
                    var online='<div class="badge mr-1 help " data-bs-toggle="tooltip" data-placement="top" title="OFFLINE"><i class="fa fa-circle text-danger"></i></div>';
                }
            
                if(x === 'TRUE'){
                    var active='';
                }
                // else if (row['data_check'] === 'off')
                else 
                {
                    var active='<div class="badge help todo-tasklist-badge badge badge-danger badge-roundless align-self-end ms-2" data-bs-toggle="tooltip" data-placement="top" title="DISABILITATO"><i class="fa-solid fa-user-xmark text-white"></i></div>'
                }
                if(y === 'on'){
                    var type_user='';
                }
                // else if (row['data_check'] === 'off')
                else 
                {
                    var type_user='<div class="badge help todo-tasklist-badge badge badge-info badge-roundless align-self-end" data-bs-toggle="tooltip" data-placement="top" title="ESTERNO"><i class="fa-solid fa-user-tag text-white"></i></div>'
                }
                //return '<a href="gestione_utente.php?id='+row[4]+'"><button id="Modifica" data-bs-toggle="tooltip" data-placement="top" data-original-title="Modifica" title="Modifica" class="btn btn-success btn-circle mr-1"><i class="fa fa-cog"></i></button></a> '+data+ active;
                return '<div class="link_in_tabella font-weight-bold d-flex align-items-center mr-auto " href="user_manager.php?manage_user=yes&uid='+row['uid']+'"> ' + online + '<div class="me-auto">'+data+'</div>' + type_user + active+'</div>';

            },
        },
        {   
            "data": "username",
            "render": function ( data, type, row ) {
                return data;
            },
        },
        {   
            "data": "phone",
            "render": function ( data, type, row ) {
                // return remove_char(data, '');
                return data;
            },
        },
        {   
            "data": "email",
            "render": function ( data, type, row ) {
                // var date_db = moment(data).format("DD/MM/YYYY - HH:mm");
                return data;
            },
        },
        {   
            "data": "uid", 
            "render": function ( data, type, row ) {
                var uid_rif = row['uid'];
                //    return "<button class='text-white btn btn-block btn-secondary btn-xs' data-toggle='modal' data-link='dettagli.php?destinazione=utente&id_rif="+row[4]+"' data-id='" + row[4] +"' data-target='#ajax' >DETTAGLI</button>";
                //    return "<a data-toggle='modal' data-link='dettagli.php?destinazione=utente&id_rif="+row[4]+"' data-id='" + row[4] +"' data-target='#ajax' ><i role='button' class='cursor-pointer fas  fa-search-plus' data-toggle='tooltip' title='Dettagli' ></i></a>";
                return   `<div class="btn-group btn-group-sm">
                                <button data-toggle='edit' data-id="${uid_rif}" id="edit" type="button" data-bs-toggle="tooltip" title="MODIFICA" class="w-25px h-25px btn-icon btn btn-sm btn-warning float-right text-uppercase">
                                    <i class="fas fa-pencil-alt text-light-warning"></i>
                                </button>
                                <button data-toggle='modal' data-link='' data-id="${uid_rif}" data-target='' id="change_user" type="button" data-bs-toggle="tooltip" title="IMPERSONA UTENTE"class="w-25px h-25px btn-icon btn btn-sm btn-primary float-right text-uppercase">
                                        <i class="fas fa-user-gear"></i>
                                </button>
                            </div>`  ;
            }  
        },
    ],
    //Ordina i record in modo crescente in base alla colonna 1
    "order": [
        [1, 'asc']
    ],   
    select: {
        style: 'multi',
        selector: 'td:first-child input[type="checkbox"]',
        className: 'row-selected'
    },

    // ajax: async function (data, callback, settings) {
    //     try {
    //         const users = await getUsersList_datatables();
    //         callback({ data: users });  // <-- DataTables expects { data: [...] }
    //     } catch (error) {
    //         console.error('Errore DataTables:', error);
    //         callback({ data: [] });
    //     }
    // },

    // ajax: async function (data, callback, settings) {
    //     try {
    //         const users = await getUsersList_datatables(currentFilters); // passa i filtri dinamici
    //         callback({ data: users });
    //     } catch (error) {
    //         console.error('Errore DataTables:', error);
    //         callback({ data: [] });
    //     }
    // },

    ajax: function (data, callback, settings) {
        getUsersList_datatables(currentFilters)
            .then(users => {
                callback({ data: users });
            })
            .catch(error => {
                console.error('Errore DataTables:', error);
                callback({ data: [] });
            });
    },
    
    "initComplete": function(settings, json){
        // generate_toolbar_row();
        // insert_button_group();
        // select_richiesta();
        // diagnosi();
        // age();

        // $start_val = [0,1]
        // $stato_richiesta.val($start_val).trigger("change");
        // $('#card_acceptance_form_list').find('#filters').find('#select_box_diagnosi, #select_box_richiesta, #age_min, #age_max').on('select2:select', function (e) {            
        //     this.table.ajax.reload();    
        // });
        // $('#card_acceptance_form_list').find('#filters').find('#select_box_diagnosi, #select_box_richiesta, #age_min, #age_max').on('select2:unselect', function (e) {
        //     this.table.ajax.reload();
        // });
        // list_acceptance_form.ajax.reload();
        // this.api = this.api();
        /**
         * Eseguo la ricerca da una select esterna dentro una colonna nascosta
         */
        // api.columns(7).every( function () {
        //     /**
        //      * imposto il valore di base della select
        //      */
        //     this
        //         .search($start_val,true, true, false)
        //         .draw();
        //     var that = this;
        //     $('#card_acceptance_form_list').find('#toolbar').find('#select_box_richiesta').on('select2:select', function (e) {            
        //         var data = e.params.data;
        //         if(that.search()){
        //             search_data = that.search()+"|"+data.id;
        //         }else{
        //             search_data = data.id;
        //         }
        //         if ( that.search() !== this.value ) {
        //             that
        //                 .search(search_data,true, true, false)
        //                 .draw();
        //         }
        //     });
        //     $('#card_acceptance_form_list').find('#toolbar').find('#select_box_richiesta').on('select2:unselect', function (e) {
        //         var data = e.params.data;
                
        //         search_data = that.search().split("|");
        //         search_data = search_data.map(Number);
        //             removeItem = data.id;
        //         array = jQuery.grep(search_data, function(value) {
        //             return value != removeItem;
        //             });
        //         var value = array;
        //         var blkstr = [];
        //         $.each(value, function(idx2,val2) {                    
        //         var str =  val2;
        //         blkstr.push(str);
        //         });
        //         var a = blkstr.join("|");
        //         console.log(a);
    
        //         if ( a !== this.value ) {
        //             that
        //             .search(a, true, false )
        //                 .draw();
        //         }
        //     });
        // });

        /**
         * Avilito la ricerca per la colonna uno creando una select
         */
        // api.columns(1)
        //     .every(function () {
        //         var column = this;
        //         var select = $('<select id="eta" class="form-control form-control-sm"><option value=""></option></select>')
        //             .appendTo($(column.footer()).empty())
        //             .on('change', function () {
        //                 var val = $.fn.dataTable.util.escapeRegex($(this).val());

        //                 column.search(val ? '^' + val + '$' : '', true, false).draw();
        //             });
        //         column
        //             .data()
        //             .unique()
        //             .sort()
        //             .each(function (d, j) {
        //                 console.log();
        //                 select.append('<option value="' + d + '">' + d + '</option>');
        //             });
        //     });

        /**
         * Abilito la ricerca per queste colonne
         */
        // api.columns()
        //     .every(function(){
        //         var that = this;
        //         $( 'input', this.footer() ).on( 'keyup change', function () {
        //             if ( that.search() !== this.value ) {
        //                 that
        //                     .search( this.value, true, false )
        //                     .draw();
        //             }
        //         });
        //     })
        // var api_html = '';
        // this.api.columns()
        //     .every(function () {
        //         // console.log($(this.header()).text())
        //         var column = this;
        //         var title = $(this.header()).text().trim();
        //         var idtitle = title.replace(/ /g,"_");
        //         if(title == ''){
                    
        //         }else{
        //             var select = $('<div class="col-12 col-xxl my-1 my-xxl-0"><input id="'+idtitle+'" class="form-control form-control-sm '+idtitle+'" type="text" placeholder="Cerca '+title+'" /></div>')
        //             .appendTo('#filter_tabella')
        //             $(select.find('input')).on('keyup change', function () {
        //                     var val = $.fn.dataTable.util.escapeRegex($(this).val());
        //                         // column.search(val ? '^' + val + '$' : '', true, false).draw();
        //                         column.search(this.value, true, false).draw();
        //                 });
        //             column
        //                 .data()
        //                 .unique()
        //                 .sort()
        //                 // .each(function (d, j) {
        //                 //     console.log();
        //                 //     select.append('<option value="' + d + '">' + d + '</option>');
        //                 // });
        //         }
        //     });
    }
})