# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import sqlalchemy as sql

from keystone.common.sql import migration_helpers
from keystone.assignment import core

_PROJECT_TABLE_NAME = 'project'
_DOMAIN_TABLE_NAME = 'domain'
_PARENT_ID_COLUMN_NAME = 'parent_id'


def list_constraints(project_table):
    constraints = [{'table': project_table,
                    'fk_column': _PARENT_ID_COLUMN_NAME,
                    'ref_column': project_table.c.id}]

    return constraints

def upgrade(migrate_engine):
    meta = sql.MetaData()
    meta.bind = migrate_engine

    project_table = sql.Table(_PROJECT_TABLE_NAME, meta, autoload=True)
    domain_table = sql.Table(_DOMAIN_TABLE_NAME, meta, autoload=True)

    projects = list(project_table.select().execute())
    domains = list(domain_table.select().execute())

    # NOTE(raildo): Remove the parent_id constraint during the migration
    # because for every root project inside this domain, we will set
    # the domain_id to be the parent_id. We enable the constraint
    # again in the end of this method.
    migration_helpers.remove_constraints(list_constraints(project_table))
    for domain in domains:
        for project in projects:
            if domain.c.name in projects.c.name:
                # TODO: We need to resolve the clashing name problem
                pass
            if domain.c.id in projects.c.id:
                # TODO: We need to resolve the clashing id problem
                pass
            if project.c.domain_id == domain.c.id and project.c.parent_id is None:
                project.c.parent_id = domain.c.id
                core.update_project(project.c.id, project)
            else:
                core.create_domain(domain.c.id, domain)

    if migrate_engine.name == 'sqlite':
        return

    migration_helpers.add_constraints(list_constraints(project_table))

def downgrade(migrate_engine):
    meta = sql.MetaData()
    meta.bind = migrate_engine

    project_table = sql.Table(_PROJECT_TABLE_NAME, meta, autoload=True)

    projects = list(project_table.select().execute())

    for project in projects:
        if project.c.id == project.c.domain_id:
            core.delete_project(project.c.id)
