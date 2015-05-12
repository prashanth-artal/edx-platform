###
E-Commerce Section
###

# Load utilities
PendingInstructorTasks = -> window.InstructorDashboard.util.PendingInstructorTasks

class ECommerce
# E-Commerce Section
  constructor: (@$section) ->
    # attach self to html so that instructor_dashboard.coffee can find
    #  this object to call event handlers like 'onClickTitle'
    @$section.data 'wrapper', @
    # gather elements
    @$list_sale_csv_btn = @$section.find("input[name='list-sale-csv']'")
    @$list_order_sale_csv_btn = @$section.find("input[name='list-order-sale-csv']'")
    @$download_company_name = @$section.find("input[name='download_company_name']'")
    @$active_company_name = @$section.find("input[name='active_company_name']'")
    @$spent_company_name = @$section.find('input[name="spent_company_name"]')
    @$download_coupon_codes = @$section.find('input[name="download-coupon-codes-csv"]')
    
    @$download_registration_codes_form = @$section.find("form#download_registration_codes")
    @$active_registration_codes_form = @$section.find("form#active_registration_codes")
    @$spent_registration_codes_form = @$section.find("form#spent_registration_codes")

    @report_downloads = new ReportDownloads(@$section)
    @instructor_tasks = new (PendingInstructorTasks()) @$section

    @$error_msg = @$section.find('#error-msg')
    
    # attach click handlers
    # this handler binds to both the download
    # and the csv button
    @$list_sale_csv_btn.click (e) =>
      url = @$list_sale_csv_btn.data 'endpoint'
      url += '/csv'
      location.href = url

    @$list_order_sale_csv_btn.click (e) =>
      url = @$list_order_sale_csv_btn.data 'endpoint'
      location.href = url

    @$download_coupon_codes.click (e) =>
      url = @$download_coupon_codes.data 'endpoint'
      location.href = url

    @$download_registration_codes_form.submit (e) =>
      @$error_msg.attr('style', 'display: none')
      return true

    @$active_registration_codes_form.submit (e) =>
      @$error_msg.attr('style', 'display: none')
      return true

    @$spent_registration_codes_form.submit (e) =>
      @$error_msg.attr('style', 'display: none')
      return true

  # handler for when the section title is clicked.
  onClickTitle: ->
    @clear_display()
    @instructor_tasks.task_poller.start()
    @report_downloads.downloads_poller.start()

  # handler for when the section is closed
  onExit: ->
    @clear_display()
    @instructor_tasks.task_poller.stop()
    @report_downloads.downloads_poller.stop()

  clear_display: ->
    @$error_msg.attr('style', 'display: none')
    @$download_company_name.val('')
    @$active_company_name.val('')
    @$spent_company_name.val('')

  isInt = (n) -> return n % 1 == 0;
    # Clear any generated tables, warning messages, etc.

class ReportDownloads
  ### Report Downloads -- links expire quickly, so we refresh every 5 mins ####
  constructor: (@$section) ->

    @$report_downloads_table = @$section.find ".report-downloads-table"

    POLL_INTERVAL = 20000 # 20 seconds, just like the "pending instructor tasks" table
    @downloads_poller = new window.InstructorDashboard.util.IntervalManager(
      POLL_INTERVAL, => @reload_report_downloads()
    )

  reload_report_downloads: ->
    endpoint = @$report_downloads_table.data 'endpoint'
    $.ajax
      dataType: 'json'
      url: endpoint
      success: (data) =>
        if data.downloads.length
          @create_report_downloads_table data.downloads
        else
          console.log "No reports ready for download"
      error: (std_ajax_err) => console.error "Error finding report downloads"

  create_report_downloads_table: (report_downloads_data) ->
    @$report_downloads_table.empty()

    options =
      enableCellNavigation: true
      enableColumnReorder: false
      rowHeight: 30
      forceFitColumns: true

    columns = [
      id: 'link'
      field: 'link'
      name: gettext('File Name')
      toolTip: gettext("Links are generated on demand and expire within 5 minutes due to the sensitive nature of student information.")
      sortable: false
      minWidth: 150
      cssClass: "file-download-link"
      formatter: (row, cell, value, columnDef, dataContext) ->
        '<a href="' + dataContext['url'] + '">' + dataContext['name'] + '</a>'
    ]

    $table_placeholder = $ '<div/>', class: 'slickgrid'
    @$report_downloads_table.append $table_placeholder
    grid = new Slick.Grid($table_placeholder, report_downloads_data, columns, options)
    grid.autosizeColumns()

# export for use
# create parent namespaces if they do not already exist.
_.defaults window, InstructorDashboard: {}
_.defaults window.InstructorDashboard, sections: {}
_.defaults window.InstructorDashboard.sections,
   ECommerce:  ECommerce