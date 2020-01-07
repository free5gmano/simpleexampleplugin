from service_mapping_plugin_framework.allocate_nssi_abc import AllocateNSSIabc
import requests
import zipfile
import json
import os


class NFVOPlugin(AllocateNSSIabc):
    def __init__(self, nm_host, nfvo_host):
        super().__init__(nm_host, nfvo_host)
        self.vnf_pkg_id = str()
        self.nsd_object_id = str()
        self.ns_descriptor_id = str()
        self.ns_instance_id = str()
        self.vnf_instance_data = list()
        self.headers = {'Content-type': 'application/json'}

    def create_vnf_package(self, vnf_pkg_path):
        # VNF Package compression
        src_path = os.getcwd()
        os.chdir(os.path.join(vnf_pkg_path))
        file_name = vnf_pkg_path.split('/')[-1]
        with zipfile.ZipFile(vnf_pkg_path + '.zip', mode='w',
                             compression=zipfile.ZIP_DEFLATED) as zf:
            for pkg_root, folders, files in os.walk('.'):
                for s_file in files:
                    a_file = os.path.join(pkg_root, s_file)
                    zf.write(a_file, arcname=os.path.join(file_name, a_file))
        os.chdir(src_path)
        # Create VNF Package
        url = self.NFVO_URL + "vnfpkgm/v1/vnf_packages/"
        data = {
            "userDefinedData": {}
        }
        create_vnfp = requests.post(url, data=json.dumps(data), headers=self.headers)
        if create_vnfp.status_code == 201:
            self.vnf_pkg_id = create_vnfp.json()['id']
            print("Vnf package ID: {}".format(self.vnf_pkg_id))
        else:
            response = {
                "attributeListOut": {
                    'create_vnf_package': create_vnfp.status_code
                },
                "status": "OperationFailed"
            }
            raise Exception(response)

    def upload_vnf_package(self, vnf_pkg_path):
        vnf_pkg_path = vnf_pkg_path + ".zip"
        file_name = vnf_pkg_path.split('/')[-1]
        print("Upload '{}' package...".format(file_name))
        url = self.NFVO_URL + "vnfpkgm/v1/vnf_packages/{}/package_content/".format(self.vnf_pkg_id)
        files = {'file': (file_name, open(vnf_pkg_path, 'rb').read(),
                          'application/zip', {'Expires': '0'})}
        headers = {
            'Accept': "application/json,application/zip",
            'accept-encoding': "gzip, deflate"
        }
        upload_vnfp = requests.put(url, files=files, headers=headers)
        if upload_vnfp.status_code == 202:
            print('Accepted')
        else:
            print('Failed')

    def create_ns_descriptor(self, ns_descriptor_path):
        # NS Description compression
        src_path = os.getcwd()
        os.chdir(os.path.join(ns_descriptor_path))
        file_name = ns_descriptor_path.split('/')[-1]
        with zipfile.ZipFile(ns_descriptor_path + '.zip', mode='w',
                             compression=zipfile.ZIP_DEFLATED) as zf:
            for pkg_root, folders, files in os.walk('.'):
                for s_file in files:
                    a_file = os.path.join(pkg_root, s_file)
                    zf.write(a_file, arcname=os.path.join(file_name, a_file))
        os.chdir(src_path)
        print("Create Network service descriptor...")
        url = self.NFVO_URL + "nsd/v1/ns_descriptors/"
        data = {
            "userDefinedData": {}
        }
        create_nsd = requests.post(url, data=json.dumps(data), headers=self.headers)
        if create_nsd.status_code == 201:
            self.nsd_object_id = create_nsd.json()['id']
        else:
            response = {
                "attributeListOut": {
                    'create_vnf_subscribe': create_nsd.status_code
                },
                "status": "OperationFailed"
            }
            raise Exception(response)

    def upload_ns_descriptor(self, ns_descriptor_path):
        ns_descriptor_path = ns_descriptor_path + ".zip"
        file_name = ns_descriptor_path.split('/')[-1]
        print(ns_descriptor_path)
        print('Upload {} descriptor file...'.format(file_name))
        url = self.NFVO_URL + "nsd/v1/ns_descriptors/{}/nsd_content/".format(self.nsd_object_id)
        files = {'file': (file_name, open(ns_descriptor_path, 'rb').read(),
                          'application/zip', {'Expires': '0'})}
        headers = {
            'Accept': "application/json,application/zip",
            'accept-encoding': "gzip, deflate"
        }
        upload_nsd = requests.put(url, files=files, headers=headers)
        print("Upload operated status {}".format(upload_nsd.status_code))
        self.read_ns_descriptor()

    def read_ns_descriptor(self):
        # None plugin inherit
        url = self.NFVO_URL + "nsd/v1/ns_descriptors/{}/".format(self.nsd_object_id)
        get_nsd = requests.get(url, headers=self.headers)
        self.ns_descriptor_id = get_nsd.json()['nsdId']
        print("Network service descriptor ID: {}".format(self.ns_descriptor_id))

    def create_ns_instance(self, ns_descriptor_path):
        print("Create Network service Instance ...")
        url = self.NFVO_URL + "nslcm/v1/ns_instances/"
        data = {
            "nsdId": self.ns_descriptor_id,
            "nsName": "string",
            "nsDescription": "string"
        }
        create_nsi = requests.post(url, data=json.dumps(data), headers=self.headers)
        if create_nsi.status_code == 201:
            self.ns_instance_id = create_nsi.json()['id']
            vnf_instance_list = create_nsi.json()['vnfInstance']
            for vnf_instance in vnf_instance_list:
                self.vnf_instance_data.append({
                    "vnfInstanceId": vnf_instance['id'],
                    "vnfProfileId": "string"
                })
        else:
            response = {
                "attributeListOut": {
                    'create_nsi': create_nsi.status_code
                },
                "status": "OperationFailed"
            }
            raise Exception(response)

    def ns_instantiation(self, ns_descriptor_path):
        print("Network service instance ID: {}".format(self.ns_instance_id))
        print("Instantiation Network service Instance ...")
        print("Vnf instance data {}".format(self.vnf_instance_data))
        url = self.NFVO_URL + "nslcm/v1/ns_instances/{}/instantiate/".format(self.ns_instance_id)
        data = {"vnfInstanceData": self.vnf_instance_data}
        instance_nsi = requests.post(url, data=json.dumps(data), headers=self.headers)
        if instance_nsi.status_code == 202:
            print('Accepted')
        else:
            print('Failed')


def main():
    nfvo_plugin = NFVOPlugin(os.environ.get('FREE5GMANO_NM'),  # NM ip
                             os.environ.get('FREE5GMANO_NFVO'))  # NFVO ip
    nfvo_plugin.allocate_nssi()


if __name__ == '__main__':
    main()
