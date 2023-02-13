import connexion
import six

from common_libs.common import *  # noqa: F403
from common_libs.api import api_filter


@api_filter
def post_cicd_for_iac_resume_filelink(organization_id, workspace_id, uuid, body=None):  # noqa: E501
    """post_cicd_for_iac_resume_filelink

    資材紐付の再開 # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param uuid: uuid
    :type uuid: str

    :rtype: InlineResponse20011
    """
    return 'do some magic!',


@api_filter
def post_cicd_for_iac_resume_repository(organization_id, workspace_id, uuid, body=None):  # noqa: E501
    """post_cicd_for_iac_resume_repository

    リモートリポジトリの再開 # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param uuid: uuid
    :type uuid: str

    :rtype: InlineResponse20011
    """
    return 'do some magic!',
