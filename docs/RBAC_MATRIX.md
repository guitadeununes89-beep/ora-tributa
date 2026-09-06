# Matriz RBAC inicial

| Papel | Ler | Avaliar | Curar | Aprovar | Publicar | Empresas | Membros |
|---|---:|---:|---:|---:|---:|---:|---:|
| VIEWER | sim | não | não | não | não | não | não |
| ANALYST | sim | sim | não | não | não | não | não |
| CURATOR | sim | não | sim | não | não | não | não |
| APPROVER | sim | não | não | sim | não | não | não |
| PUBLISHER | sim | não | não | não | sim | não | não |
| ADMIN | sim | não | não | não | não | sim | sim |

A segregação entre curadoria, aprovação e publicação é deliberada. Quando a política de SoD está
habilitada, o serviço também impede que o mesmo ator execute transições incompatíveis no ciclo de
vida. A autorização por papel e a SoD são controles complementares.

