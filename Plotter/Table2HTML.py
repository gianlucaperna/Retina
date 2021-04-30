def table(df, text, software, flow=False):
    try:
        html = """
        <!doctype html>
        <html lang="en">
          <head>
            <!-- Required meta tags -->
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">

            <!-- Bootstrap CSS -->
            <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">

            <title>Retina Plot</title>
          </head>
          <body>
            <!-- Optional JavaScript -->
            <!-- jQuery first, then Popper.js, then Bootstrap JS -->
            <script src="https://code.jquery.com/jquery-3.2.1.slim.min.js" integrity="sha384-KJ3o2DKtIkvYIK3UENzmM7KCkRr/rE9/Qpg6aAZGJwFDMVNA/GpGFF93hXpG5KkN" crossorigin="anonymous"></script>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.12.9/umd/popper.min.js" integrity="sha384-ApNbgh9B+Y1QKtv3Rn7W3mgPxhU9K/ScQsAP7hUibX39j7fakFPskvXusvfa0b4Q" crossorigin="anonymous"></script>
            <script src="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/js/bootstrap.min.js" integrity="sha384-JZR6Spejh4U02d8jOt6vLEHfe/JQGiRRSQQxSfFWpi1MquVdAyjUar5+76PVCmYl" crossorigin="anonymous"></script>

            <nav class="navbar navbar-dark bg-dark">
                <h4 class="text-white text-center">RETINA: """ + text + """<h4>
            </nav>

            <div class="container-fluid pt-5">
                <div class="row ">
                    <div class="mx-auto col-8">
                        <table class="table table-striped">
                        <thead>
                        <tr>
                          <th scope="col">Flow </th>
                          <th scope="col">SSRC</th>
                          <th scope="col">IP src</th>
                          <th scope="col">IP dst</th>
                          <th scope="col">Port Src</th>
                          <th scope="col">Port dst</th>
                          """
        if software != "msteams" and software != "skype":
                html+= """<th scope="col">PT</th>"""

        html+= """ <th scope="col">CSRC</th>
                          <th scope="col">Label</th>
                        </tr>
                        </thead>
                        <tbody>
                    """

        for row in df.itertuples():
            html += """<tr>"""
            if (flow):
                html += """<th scope="row">""" + str(row.Index) + """</th>"""
            else:
                html += """<th scope="row">-</th>"""
            html += """<td>""" + str(row.ssrc) + """</td>""" + \
                    """<td>""" + str(row.source_addr) + """</td>""" + \
                    """<td>""" + str(row.dest_addr) + """</td>""" + \
                    """<td>""" + str(row.source_port) + """</td>""" + \
                    """<td>""" + str(row.dest_port) + """</td>""" + \
                    """<td>""" + str(row.csrc) + """</td>""" + \
                    """ <td>""" + str(row.label) + """</td> """
            if software != "msteams" and software != "skype":
                html +=  """<td>""" + str(row.rtp_p_type) + """</td>"""
            html += """</tr>"""
        html += """
                        </tbody>
                        </table>
                    </div>
                </div>
            </div>
        """
        return html
    except Exception as e:
        print(e)
