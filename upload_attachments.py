#!/usr/bin/env python

# This has to run as user omero-server.
# Assumes that omero-upload was installed on the server.
# cp attachments.csv /tmp
# cp upload_attachments.py /tmp
# chmod +x /tmp/upload_attachments.py
# sudo su omero-server
# cd /tmp
# . /opt/omero/server/venv3/bin/activate
# python upload_attachments.py


import omero.clients
import omero.cli
from omero_upload import upload_ln_s

project_id = 1451
attachment_file = "/tmp/attachments.csv"
link_to_image = True
image_ending_right = False
image_matches_attachment = False

OMERO_DATA_DIR = '/data/OMERO'
NAMESPACE = 'openmicroscopy.org/idr/analysis/original'
MIMETYPE = 'application/octet-stream'

print("Project id: %d, \
      attachment file: %s, \
      link_to_image: %s, \
      data dir: %s, \
      namespace: %s, \
      mimetype: %s" %
      (project_id, attachment_file, str(link_to_image),
       OMERO_DATA_DIR, NAMESPACE, MIMETYPE))

input("Press key to continue")


def link(conn, target, attachment, is_image):
    fo = upload_ln_s(conn.c, attachment, OMERO_DATA_DIR, MIMETYPE)
    fa = omero.model.FileAnnotationI()
    fa.setFile(fo._obj)
    fa.setNs(omero.rtypes.rstring(NAMESPACE))
    fa = conn.getUpdateService().saveAndReturnObject(fa)
    fa = omero.gateway.FileAnnotationWrapper(conn, fa)
    if is_image:
        tg = conn.getObject("Image", target.getId().getValue())
        tg.linkAnnotation(fa)
    else:
        for d in target:
            tg = conn.getObject("Dataset", d.getId().getValue())
            tg.linkAnnotation(fa)


def process_line(conn, project, line, link_image, count):
    # /uod/idr/filesets/idr0082-pennycuick-lesions/20200417-ftp/S1_HandE.ndpi.ndpa
    # /uod/idr/filesets/idr0082-pennycuick-lesions/20200417-ftp/S2_HandE.ndpi.ndpa
    parts = line.split(',')
#    dataset_name = "Desktop"

    datasets = []
    for dataset in project.linkedDatasetList():
        print(dataset.getName().getValue())
        if link_image:
            for image in dataset.linkedImageList():
                image_name = image.getName().getValue()
                length = len(parts)
                attachment_path = parts[0]
                image_name_matches = (parts[length - 1] == image_name)
                if (image_name_matches):
                    link(conn, image, attachment_path, link_image)
                    print("Linked attachment %s to image %s" %
                            (attachment_path, image.getName().getValue()))
#        elif dataset.getName().getValue().startswith(dataset_name):
#            datasets.append(dataset)

    if len(datasets) > 0:
        link(conn, datasets, attachment_path, link_image)
        print("Linked attachment %s to %d datasets" % (attachment_path, len(datasets)))


def main(conn):
    with open(attachment_file) as fp:
        cs = conn.getContainerService()
        param = omero.sys.ParametersI().leaves()
        project = cs.loadContainerHierarchy("Project", [project_id], param)[0]

        line = fp.readline().strip()
        count = 0
        while line and len(line) > 0:
            count += 1
            print("Line %d" % count)
            process_line(conn, project, line, link_to_image, count)
            line = fp.readline().strip()


if __name__ == '__main__':
    with omero.cli.cli_login() as c:
        conn = omero.gateway.BlitzGateway(client_obj=c.get_client())
        main(conn)
