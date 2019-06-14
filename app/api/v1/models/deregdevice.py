"""
DRS De-Registration Device Model package.
SPDX-License-Identifier: BSD-4-Clause-Clear
Copyright (c) 2018-2019 Qualcomm Technologies, Inc.
All rights reserved.
Redistribution and use in source and binary forms, with or without modification, are permitted (subject to the limitations in the disclaimer below) provided that the following conditions are met:
    Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
    Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
    All advertising materials mentioning features or use of this software, or any deployment of this software, or documentation accompanying any distribution of this software, must display the trademark/logo as per the details provided here: https://www.qualcomm.com/documents/dirbs-logo-and-brand-guidelines
    Neither the name of Qualcomm Technologies, Inc. nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
SPDX-License-Identifier: ZLIB-ACKNOWLEDGEMENT
Copyright (c) 2018-2019 Qualcomm Technologies, Inc.
This software is provided 'as-is', without any express or implied warranty. In no event will the authors be held liable for any damages arising from the use of this software.
Permission is granted to anyone to use this software for any purpose, including commercial applications, and to alter it and redistribute it freely, subject to the following restrictions:
    The origin of this software must not be misrepresented; you must not claim that you wrote the original software. If you use this software in a product, an acknowledgment is required by displaying the trademark/logo as per the details provided here: https://www.qualcomm.com/documents/dirbs-logo-and-brand-guidelines
    Altered source versions must be plainly marked as such, and must not be misrepresented as being the original software.
    This notice may not be removed or altered from any source distribution.
NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
from app import db, app
from app.api.v1.models.deregimei import DeRegImei
from app.api.v1.helpers.utilities import Utilities
import json
import threading
from app.api.v1.models.deregdetails import DeRegDetails


class DeRegDevice(db.Model):
    """Database model for deregdevice table."""
    __tablename__ = 'deregdevice'

    id = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(1000))
    model_name = db.Column(db.String(1000), nullable=False)
    model_num = db.Column(db.String(1000), nullable=False)
    operating_system = db.Column(db.String(1000), nullable=False)
    device_type = db.Column(db.String(1000), nullable=False)
    technology = db.Column(db.String(1000), nullable=False)
    device_count = db.Column(db.Integer, nullable=False)
    tac = db.Column(db.String(8))

    dereg_details_id = db.Column(db.Integer, db.ForeignKey('deregdetails.id'))
    dereg_device_imei = db.relationship('DeRegImei', backref='deregdevice', passive_deletes=True, lazy=True)

    def __init__(self, args):
        """Constructor."""
        self.brand = args.get('brand_name')
        self.model_name = args.get('model_name')
        self.model_num = args.get('model_num')
        self.operating_system = args.get('operating_system')
        self.device_type = args.get('device_type')
        self.technology = args.get('technology')
        self.device_count = args.get('count')
        self.tac = args.get('tac')

    @classmethod
    def create_index(cls, engine):
        """ Create Indexes for De-Registration device table. """

        # brand_index = db.Index('dereg_device_brand', cls.brand)
        # brand_index.create(bind=engine)

        # model_name_index = db.Index('dereg__device_model_name', cls.model_name)
        # model_name_index.create(bind=engine)

        # model_number_index = db.Index('dereg_device_model_number', cls.model_num)
        # model_number_index.create(bind=engine)

        # operating_system_index = db.Index('dereg_device_os', cls.operating_system)
        # operating_system_index.create(bind=engine)

        # device_type_index = db.Index('dereg_device_type', cls.device_type)
        # device_type_index.create(bind=engine)

        # technology_index = db.Index('dereg_device_technology', cls.technology)
        # technology_index.create(bind=engine)

        # tac_index = db.Index('dereg_device_tac', cls.tac)
        # tac_index.create(bind=engine)

    @classmethod
    def curate_args(cls, args, dereg):
        """Curate http request args."""
        if 'devices' in args:
            args['devices'] = json.loads(args.get('devices', []))
        if dereg:
            args['dereg_id'] = dereg.id
        else:
            args['dereg_id'] = ''
        return args

    @classmethod
    def create(cls, args, dereg_id):
        """Create a new de registration device."""
        device = DeRegDevice(args)
        device.dereg_details_id = dereg_id
        device.save()
        return device

    @classmethod
    def bulk_insert_imeis(cls, devices, imei_tac_map, old_devices, imeis_list, dereg):
        """Insert IMEIs in bulk."""
        try:
            dereg.update_processing_status('Processing')
            db.session.commit()
            thread = threading.Thread(daemon=True, target=cls.async_create, args=(devices, imei_tac_map, old_devices,
                                                                                  dereg.id, imeis_list, app))
            thread.start()
        except Exception as e:
            app.logger.exception(e)
            dereg.update_processing_status('Failed')
            db.session.commit()

    @classmethod
    def bulk_create(cls, args, dereg):
        """Create devices in bulk."""
        created_devices = []
        for device_arg in args.get('devices'):
            device = cls.create(device_arg, dereg.id)
            created_devices.append(device)
        return created_devices

    @classmethod
    def async_create(cls, devices, imei_tac_map, old_devices, dereg_id, imeis_list, app):
        """Async create a new device."""
        with app.app_context():
            from app import db
            dereg = DeRegDetails.get_by_id(dereg_id)
            try:
                DeRegDevice.clear_devices(old_devices)
                for device in devices:
                    device_imeis = imei_tac_map.get(device.get('tac'))
                    dereg_imei_list = DeRegImei.get_deregimei_list(device.get('id'), device_imeis)
                    res = db.engine.execute(DeRegImei.__table__.insert(), dereg_imei_list)
                    res.close()
                dereg.update_processing_status('Processed')
                db.session.commit()
                task_id = Utilities.generate_summary(imeis_list, dereg.tracking_id)
                Utilities.pool_summary_request(task_id, dereg, app)
            except Exception as e:
                app.logger.exception(e)
                dereg.update_processing_status('Failed')
                db.session.commit()

    def save(self):
        """Save the current state of the model."""
        try:
            db.session.add(self)
            db.session.flush()
        except Exception:
            db.session.rollback()
            raise Exception

    @classmethod
    def get_devices_by_dereg_id(cls, dreg_id):
        """Get devices by de registration request id."""
        devices = cls.query.filter_by(dereg_details_id=dreg_id).all()
        return devices

    @classmethod
    def get_devices_id_by_dereg_id(cls, dreg_id):
        """Get devices ids by request id."""
        devices = cls.query.filter_by(dereg_details_id=dreg_id).all()
        devices_ids = list(map(lambda x: x.id, devices))
        return devices_ids

    @classmethod
    def clear_devices(cls, old_devices):
        """Clear old devices of the request."""
        # device_ids = map(lambda device: device.id, old_devices)
        stmt = cls.__table__.delete().where(cls.id.in_(old_devices))
        res = db.engine.execute(stmt)
        res.close()

    @classmethod
    def get_by_id(cls, dereg_device_id):
        """Get device by id."""
        return cls.query.filter_by(id=dereg_device_id).first()
