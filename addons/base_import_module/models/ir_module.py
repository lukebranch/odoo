# -*- coding: utf-8 -*-
import logging
import os
import sys
import zipfile
from os.path import join as opj

import openerp
from openerp import _, models
from openerp.tools import convert_file
from openerp.exceptions import UserError

_logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 100 * 1024 * 1024  # in megabytes


class View(models.Model):
    _inherit = "ir.module.module"

    def import_module(self, module, path, force=False):
        terp = openerp.modules.load_information_from_description_file(module, mod_path=path)
        values = self.get_values_from_terp(terp)

        unmet_dependencies = self.search([('name', 'in', terp['depends']), ('state', '!=', 'installed')])
        if unmet_dependencies:
            msg = _("Unmet module dependencies: %s")
            raise UserError(msg % ', '.join([x.name for x in unmet_dependencies]))

        mod = self.search([('name', '=', module)])
        if mod:
            mod.write(dict(state='installed', **values))
            mode = 'update' if not force else 'init'
        else:
            assert terp.get('installable', True), "Module not installable"
            self.create(dict(name=module, state='installed', **values))
            mode = 'init'

        for kind in ['data', 'init_xml', 'update_xml']:
            for filename in terp[kind]:
                _logger.info("module %s: loading %s", module, filename)
                noupdate = False
                if filename.endswith('.csv') and kind in ('init', 'init_xml'):
                    noupdate = True
                pathname = opj(path, filename)
                idref = {}
                convert_file(self.env.cr, module, filename, idref, mode=mode, noupdate=noupdate, kind=kind, pathname=pathname)

        path_static = opj(path, 'static')
        IrAttachment = self.env['ir.attachment']
        if os.path.isdir(path_static):
            for root, dirs, files in os.walk(path_static):
                for static_file in files:
                    full_path = opj(root, static_file)
                    with open(full_path, 'r') as fp:
                        data = fp.read().encode('base64')
                    url_path = '/%s%s' % (module, full_path.split(path)[1].replace(os.path.sep, '/'))
                    url_path = url_path.decode(sys.getfilesystemencoding())
                    filename = os.path.split(url_path)[1]
                    values = dict(
                        name=filename,
                        datas_fname=filename,
                        url=url_path,
                        res_model='ir.ui.view',
                        type='binary',
                        datas=data,
                    )
                    attachment = IrAttachment.search([('url', '=', url_path), ('type', '=', 'binary'), ('res_model', '=', 'ir.ui.view')])
                    if attachment:
                        attachment.write(values)
                    else:
                        IrAttachment.create(values)

        return True

    def import_zipfile(self, module_file, force=False):
        if not module_file:
            raise Exception("No file sent.")
        if not zipfile.is_zipfile(module_file):
            raise UserError(_('File is not a zip file!'))

        success = []
        errors = dict()
        module_names = []
        with zipfile.ZipFile(module_file, "r") as z:
            for zf in z.filelist:
                if zf.file_size > MAX_FILE_SIZE:
                    msg = _("File '%s' exceed maximum allowed file size")
                    raise UserError(msg % zf.filename)

            with openerp.tools.osutil.tempdir() as module_dir:
                z.extractall(module_dir)
                dirs = [d for d in os.listdir(module_dir) if os.path.isdir(opj(module_dir, d))]
                for mod_name in dirs:
                    module_names.append(mod_name)
                    try:
                        # assert mod_name.startswith('theme_')
                        path = opj(module_dir, mod_name)
                        self.import_module(mod_name, path, force=force)
                        success.append(mod_name)
                    except Exception, e:
                        errors[mod_name] = str(e)
        r = ["Successfully imported module '%s'" % mod for mod in success]
        for mod, error in errors.items():
            r.append("Error while importing module '%s': %r" % (mod, error))
        return '\n'.join(r), module_names
