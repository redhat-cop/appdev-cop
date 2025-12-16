# RHBK collection

## Dependencies

A requirement file is provided to install:
```bash
pip install -r requirements.txt
```

You also need to ansible-galaxy collection install both collections listing here:

- redhat.rhel_system_roles (version 1.108.6)
- redhat.runtimes_common (version 1.2.2)

Then you can run:

```bash
ansible-galaxy collection install redhat.rhbk
```

After that to use the collection:

```bash
---
collections:
  - name: redhat.rhbk

or

  roles:
    - role: redhat.rhbk.rhbk_realm
      rhbk_realm: TestRealm
```

