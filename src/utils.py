from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import requests
import os
import logging
import json
import datetime
import semantic_version as sv

logger = logging.getLogger(__name__)

GREMLIN_SERVER_URL_REST = "http://{host}:{port}".format(
    host=os.environ.get("BAYESIAN_GREMLIN_HTTP_SERVICE_HOST", "localhost"),
    port=os.environ.get("BAYESIAN_GREMLIN_HTTP_SERVICE_PORT", "8182"))

LICENSE_SCORING_URL_REST = "http://{host}:{port}".format(
    host=os.environ.get("LICENSE_SERVICE_HOST"),
    port=os.environ.get("LICENSE_SERVICE_PORT"))

# TO BE REMOVED
GREMLIN_SERVER_URL_REST = 'http://bayesian-gremlin-http-preview-b6ff-bayesian-preview.b6ff.rh-idev.openshiftapps.com'
LICENSE_SCORING_URL_REST = 'http://bayesian-license-scoring-bayesian-preview.b6ff.rh-idev.openshiftapps.com'
# TO BE REMOVED


# Create Postgres Connection Session
class Postgres:
    def __init__(self):
        self.connection = 'postgresql://{user}:{password}@{pgbouncer_host}:{pgbouncer_port}' \
                          '/{database}?sslmode=disable'. \
            format(user=os.environ.get('POSTGRESQL_USER'),
                   password=os.environ.get('POSTGRESQL_PASSWORD'),
                   pgbouncer_host=os.environ.get('PGBOUNCER_SERVICE_HOST', 'coreapi-pgbouncer'),
                   pgbouncer_port=os.environ.get('PGBOUNCER_SERVICE_PORT', '5432'),
                   database=os.environ.get('POSTGRESQL_DATABASE'))
        engine = create_engine(self.connection)

        self.Session = sessionmaker(bind=engine)
        self.session = self.Session()

    def session(self):
        return self.session


def get_osio_user_count(ecosystem, name, version):
    str_gremlin = "g.V().has('pecosystem','{}').has('pname','{}').has('version','{}').".format(
        ecosystem, name, version)
    str_gremlin += "in('uses').count();"
    payload = {
        'gremlin': str_gremlin
    }

    try:
        response = get_session_retry().post(GREMLIN_SERVER_URL_REST, data=json.dumps(payload))
        json_response = response.json()
        return json_response['result']['data'][0]
    except Exception:
        logger.error("Failed retrieving Gremlin data.")
        return -1


def create_package_dict(graph_results, alt_dict=None):
    """Convert Graph Results into the Recommendation Dict."""
    pkg_list = []

    for epv in graph_results:
        ecosystem = epv.get('ver', {}).get('pecosystem', [''])[0]
        name = epv.get('ver', {}).get('pname', [''])[0]
        version = epv.get('ver', {}).get('version', [''])[0]
        if ecosystem and name and version:
            # TODO change this logic later to fetch osio_user_count
            osio_user_count = get_osio_user_count(ecosystem, name, version)
            pkg_dict = {
                'ecosystem': ecosystem,
                'name': name,
                'version': version,
                'licenses': epv['ver'].get('declared_licenses', []),
                'latest_version': select_latest_version(
                    epv['pkg'].get('libio_latest_version', [''])[0],
                    epv['pkg'].get('latest_version', [''])[0]),
                'security': [],
                'osio_user_count': osio_user_count,
                'topic_list': epv['pkg'].get('pgm_topics', []),
                'cooccurrence_probability': epv['pkg'].get('cooccurrence_probability', 0),
                'cooccurrence_count': epv['pkg'].get('cooccurrence_count', 0)
            }

            github_dict = {
                'dependent_projects': epv['pkg'].get('libio_dependents_projects', [-1])[0],
                'dependent_repos': epv['pkg'].get('libio_dependents_repos', [-1])[0],
                'used_by': [],
                'total_releases': epv['pkg'].get('libio_total_releases', [-1])[0],
                'latest_release_duration': str(datetime.datetime.fromtimestamp(
                    epv['pkg'].get('libio_latest_release',
                                   [1496302486.0])[0])),
                'first_release_date': 'N/A',
                'forks_count': epv['pkg'].get('gh_forks', [-1])[0],
                'stargazers_count': epv['pkg'].get('gh_stargazers', [-1])[0],
                'watchers': epv['pkg'].get('gh_subscribers_count', [-1])[0],
                'contributors': -1,
                'size': 'N/A',
                'issues': {
                    'month': {
                        'closed': epv['pkg'].get('gh_issues_last_month_closed', [-1])[0],
                        'opened': epv['pkg'].get('gh_issues_last_month_opened', [-1])[0]
                    },
                    'year': {
                        'closed': epv['pkg'].get('gh_issues_last_year_closed', [-1])[0],
                        'opened': epv['pkg'].get('gh_issues_last_year_opened', [-1])[0]
                    }
                },
                'pull_requests': {
                    'month': {
                        'closed': epv['pkg'].get('gh_prs_last_month_closed', [-1])[0],
                        'opened': epv['pkg'].get('gh_prs_last_month_opened', [-1])[0]
                    },
                    'year': {
                        'closed': epv['pkg'].get('gh_prs_last_year_closed', [-1])[0],
                        'opened': epv['pkg'].get('gh_prs_last_year_opened', [-1])[0]
                    }
                }
            }
            used_by = epv['pkg'].get("libio_usedby", [])
            used_by_list = []
            for epvs in used_by:
                slc = epvs.split(':')
                used_by_dict = {
                    'name': slc[0],
                    'stars': int(slc[1])
                }
                used_by_list.append(used_by_dict)
            github_dict['used_by'] = used_by_list
            pkg_dict['github'] = github_dict
            pkg_dict['code_metrics'] = {
                "average_cyclomatic_complexity":
                    epv['ver'].get('cm_avg_cyclomatic_complexity', [-1])[0],
                "code_lines": epv['ver'].get('cm_loc', [-1])[0],
                "total_files": epv['ver'].get('cm_num_files', [-1])[0]
            }

            if alt_dict is not None and name in alt_dict:
                pkg_dict['replaces'] = [{
                    'name': alt_dict[name]['replaces'],
                    'version': alt_dict[name]['version']
                }]

            pkg_list.append(pkg_dict)
    return pkg_list


def select_latest_version(libio, anitya):
    libio_latest_version = libio if libio else '0.0.0'
    anitya_latest_version = anitya if anitya else '0.0.0'
    libio_latest_version = libio_latest_version.replace('.', '-', 3)
    libio_latest_version = libio_latest_version.replace('-', '.', 2)
    anitya_latest_version = anitya_latest_version.replace('.', '-', 3)
    anitya_latest_version = anitya_latest_version.replace('-', '.', 2)
    try:
        latest_version = libio if libio else ''
        if sv.SpecItem('<' + anitya_latest_version).match(sv.Version(libio_latest_version)):
            latest_version = anitya
    except ValueError:
        pass

    return latest_version


def get_session_retry(retries=3, backoff_factor=0.2, status_forcelist=(404, 500, 502, 504),
                      session=None):
    """Set HTTP Adapter with retries to session."""
    session = session or requests.Session()
    retry = Retry(total=retries, read=retries, connect=retries,
                  backoff_factor=backoff_factor, status_forcelist=status_forcelist)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    return session
