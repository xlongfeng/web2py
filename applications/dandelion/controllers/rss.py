# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This is a sample controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
## - call exposes all registered services (none by default)
#########################################################################

import os
import cgi
import cStringIO
import base64
import zlib
import xml.etree.ElementTree as ET

def index():
    grid = SQLFORM.grid(db.ebay_item_rss, links=[dict(header='', body=lambda row:A(T('Preview'),_href=URL('rss','preview',args=[base64.b64encode(row.sku)])))])
    
    web2py_runtime_gae = request.env.web2py_runtime_gae

    return dict(message=T('eBay item rss'), grid=grid, web2py_runtime_gae=web2py_runtime_gae)

def preview():
    items = []
    try:
        sku = base64.b64decode(request.args[0])
    except TypeError:
        return ''
    
    myrecord = db.ebay_item_rss(sku=sku)
    
    try:
        root = ET.fromstring(myrecord.rss)
        for child in root[0]:
            if child.tag == 'item':
                item = dict()
                for subitem in child:
                    item[subitem.tag] = subitem.text
                items.append(item)
    except:
        return ''
    
    response.headers['Access-Control-Allow-Origin'] = "*"
    return dict(items=items)

def save_csv_zip(content):
    csv = zlib.decompress(content, 16+zlib.MAX_WBITS)
    db.ebay_item_rss.truncate();
    db.commit();
    db.ebay_item_rss.import_from_csv_file(cStringIO.StringIO(csv))

def upload():
    form = SQLFORM.factory(Field('import_file', 'upload', uploadfolder=os.path.join(request.folder,'uploads')))

    if request.env.web2py_runtime_gae: 
        from google.appengine.ext import blobstore
        upload_url = blobstore.create_upload_url(URL(r=request,c='rss',f='gaeupload'))
        form['_action']=upload_url
        
    if form.process().accepted:
        file = request.vars.import_file
        if isinstance(file, cgi.FieldStorage):
            try:
                save_csv_zip(file.value)
            except:
                response.flash = T('Import rss file failed')
            else:
                response.flash = T('Import rss file success')
    elif form.errors:
        response.flash = T('form has errors')
        
    return dict(message=T('Upload rss file'), form=form)

def gaeupload():
    if request.env.web2py_runtime_gae:
        from google.appengine.ext import blobstore
        from google.appengine.ext import webapp
        from google.appengine.ext.webapp import blobstore_handlers
        from google.appengine.ext.webapp.util import run_wsgi_app
        #define WSGI request handler for upload 
        class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):
            def post(self):
                upload_files = self.get_uploads('import_file')
                blob_info = upload_files[0]
                globals()['blob_info'] = blob_info

        #create wsgi application
        application = webapp.WSGIApplication([(request.env.path_info, UploadHandler)],debug=True)
        application(request.wsgi.environ,request.wsgi.start_response)

        blob_info = globals()['blob_info']
        start=0
        end=blobstore.MAX_BLOB_FETCH_SIZE-1
        read_content=blobstore.fetch_data(blob_info.key(), start, end)
        blobstore.delete(blob_info.key())
        
        try:
            save_csv_zip(read_content)
        except:
            response.flash = T('Import rss file failed')
        else:
            response.flash = T('Import rss file success')
        
    return dict(message=T('Upload rss file'))

def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    http://..../[app]/default/user/manage_users (requires membership in
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    """
    return dict(form=auth())

@cache.action()
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()


@auth.requires_signature()
def data():
    """
    http://..../[app]/default/data/tables
    http://..../[app]/default/data/create/[table]
    http://..../[app]/default/data/read/[table]/[id]
    http://..../[app]/default/data/update/[table]/[id]
    http://..../[app]/default/data/delete/[table]/[id]
    http://..../[app]/default/data/select/[table]
    http://..../[app]/default/data/search/[table]
    but URLs must be signed, i.e. linked with
      A('table',_href=URL('data/tables',user_signature=True))
    or with the signed load operator
      LOAD('default','data.load',args='tables',ajax=True,user_signature=True)
    """
    return dict(form=crud())
