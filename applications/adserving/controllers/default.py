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
import zlib
import xml.etree.ElementTree as ET

def index():
    """
    example action using the internationalization operator T and flash
    rendered by views/default/index.html or views/generic.html

    if you need a simple wiki simply replace the two lines below with:
    return auth.wiki()
    """
    #response.flash = T("Welcome to web2py!")
    
    form = SQLFORM.factory(Field('import_file', 'upload', uploadfolder=os.path.join(request.folder,'uploads')))

    if request.env.web2py_runtime_gae: 
        from google.appengine.ext import blobstore
        upload_url = blobstore.create_upload_url(URL(r=request,c='default',f='upload'))
        form['_action']=upload_url

    ads_cvs = ''
    if form.process().accepted:
        file = request.vars.import_file
        if isinstance(file, cgi.FieldStorage):
            try:
                ads_cvs = zlib.decompress(file.value, 16+zlib.MAX_WBITS)
            except:
                response.flash = T('Import file failed')
            else:
                db.listing_ads.truncate();
                db.commit();
                db.listing_ads.import_from_csv_file(cStringIO.StringIO(ads_cvs))
                response.flash = T('Import file success')
    elif form.errors:
        response.flash = T('form has errors')
        
    grid = SQLFORM.grid(db.listing_ads, links=[dict(header='ADS', body=lambda row:A(T('View ADS'),_href=URL('default','ads',args=[row.sku])))])

    return dict(message=T('Hello World'), form=form, grid=grid)

def upload():
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
        
        ads_cvs = ''
        try:
            ads_cvs = zlib.decompress(read_content, 16+zlib.MAX_WBITS)
        except:
            return 'upload failed'
        else:
            db.listing_ads.truncate();
            db.commit();
            db.listing_ads.import_from_csv_file(cStringIO.StringIO(ads_cvs))
        
    return 'upload ok'

def ads():
    items = []
    sku = request.args[0]
    myrecord = db.listing_ads(sku=sku)
    
    try:
        root = ET.fromstring(myrecord.rss)
        for child in root[0]:
            if child.tag == 'item':
                item = dict()
                for subitem in child:
                    item[subitem.tag] = subitem.text
                items.append(item)
    except:
        return T('parse xml error')
                
    return dict(items=items)

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
