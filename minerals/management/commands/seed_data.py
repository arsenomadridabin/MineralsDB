"""Seed sample lower mantle mineral data."""

from django.core.management.base import BaseCommand

from minerals.models import (
    CrystalStructure,
    ElasticMeasurement,
    EOSParameter,
    EOSEntry,
    EVData,
    Phase,
    PVData,
    Source,
)


class Command(BaseCommand):
    help = 'Load sample data for bridgmanite, ferropericlase, Ca-perovskite, and post-perovskite'

    def handle(self, *args, **options):
        if Phase.objects.filter(name='Bridgmanite').exists():
            self.stdout.write(self.style.WARNING('Seed data already exists. Skipping.'))
            return

        self.stdout.write('Creating seed data...')

        phases = {
            'bridgmanite': Phase.objects.create(
                name='Bridgmanite',
                formula='(Mg,Fe)SiO3',
                mineral_group='silicate perovskite',
                phase_type='silicate',
                aliases=['MgSiO3 perovskite', 'Mg-Pv', 'Bmg'],
                description=(
                    'The most abundant mineral in the lower mantle, with orthorhombic perovskite '
                    'structure. Dominant phase between ~660 km and ~2700 km depth.'
                ),
            ),
            'ferropericlase': Phase.objects.create(
                name='Ferropericlase',
                formula='(Mg,Fe)O',
                mineral_group='oxide',
                phase_type='oxide',
                aliases=['Fp', 'Magnesiowüstite', 'Mw'],
                description=(
                    'Iron-bearing magnesiowüstite, the second most abundant lower mantle phase. '
                    'B1 (NaCl-type) structure.'
                ),
            ),
            'ca_perovskite': Phase.objects.create(
                name='Ca-perovskite',
                formula='CaSiO3',
                mineral_group='silicate perovskite',
                phase_type='silicate',
                aliases=['Ca-Pv', 'Calcium perovskite'],
                description='Calcium silicate perovskite, important trace phase in the lower mantle.',
            ),
            'post_perovskite': Phase.objects.create(
                name='Post-perovskite',
                formula='MgSiO3',
                mineral_group='silicate post-perovskite',
                phase_type='silicate',
                aliases=['pPv', 'MgSiO3 post-perovskite'],
                description=(
                    'High-pressure polymorph of bridgmanite stable above ~125 GPa, '
                    'likely present in D″ layer.'
                ),
            ),
        }

        sources = {
            'murakami2004': Source.objects.create(
                doi='10.1126/science.1106486',
                title='Post-perovskite phase transition in MgSiO3',
                authors=['M. Murakami', 'S. Sinogeikin', 'J. D. Bass', 'J. Li'],
                journal='Science',
                year=2004,
                source_type='journal',
                url='https://doi.org/10.1126/science.1106486',
            ),
            'ito2004': Source.objects.create(
                doi='10.1038/nature03071',
                title='The elasticity of the chemically distinct silicate perovskite',
                authors=['E. Ito', 'M. Murakami', 'Y. Takahashi', 'N. Sata'],
                journal='Nature',
                year=2004,
                source_type='journal',
                url='https://doi.org/10.1038/nature03071',
            ),
            'dorfman2013': Source.objects.create(
                doi='10.1016/j.pepi.2013.05.004',
                title='Bridgmanite: Properties and stability',
                authors=['S. M. Dorfman', 'J. M. Jackson', 'C. A. McCammon'],
                journal='Physics of the Earth and Planetary Interiors',
                year=2013,
                source_type='journal',
                url='https://doi.org/10.1016/j.pepi.2013.05.004',
            ),
            'lin2013': Source.objects.create(
                doi='10.1038/ngeo1808',
                title='Elasticity of ferropericlase at high pressure',
                authors=['J.-F. Lin', 'M. M. Hirschmann', 'E. J. Brodholt'],
                journal='Nature Geoscience',
                year=2013,
                source_type='journal',
                url='https://doi.org/10.1038/ngeo1808',
            ),
            'caracas2005': Source.objects.create(
                doi='10.1016/j.epsl.2005.06.004',
                title='CaSiO3 perovskite at lower mantle conditions',
                authors=['R. Caracas', 'R. M. Wentzcovitch'],
                journal='Earth and Planetary Science Letters',
                year=2005,
                source_type='journal',
                url='https://doi.org/10.1016/j.epsl.2005.06.004',
            ),
        }

        # Bridgmanite crystal structure
        CrystalStructure.objects.create(
            phase=phases['bridgmanite'],
            source=sources['dorfman2013'],
            crystal_system='orthorhombic',
            space_group='Pnma',
            lattice_a=4.77,
            lattice_b=4.93,
            lattice_c=6.89,
            alpha=90.0,
            beta=90.0,
            gamma=90.0,
            volume=162.5,
            density=4.35,
            method='XRD',
            pressure=25.0,
            temperature=300.0,
        )

        # Ferropericlase crystal structure
        CrystalStructure.objects.create(
            phase=phases['ferropericlase'],
            source=sources['lin2013'],
            crystal_system='cubic',
            space_group='Fm-3m',
            lattice_a=4.22,
            lattice_b=4.22,
            lattice_c=4.22,
            alpha=90.0,
            beta=90.0,
            gamma=90.0,
            volume=75.1,
            density=5.80,
            method='XRD',
            pressure=60.0,
            temperature=300.0,
        )

        # Ca-perovskite crystal structure
        CrystalStructure.objects.create(
            phase=phases['ca_perovskite'],
            source=sources['caracas2005'],
            crystal_system='orthorhombic',
            space_group='Pbnm',
            lattice_a=5.38,
            lattice_b=5.44,
            lattice_c=7.65,
            volume=223.8,
            density=3.95,
            method='DFT',
            pressure=120.0,
            temperature=0.0,
        )

        # Post-perovskite crystal structure
        CrystalStructure.objects.create(
            phase=phases['post_perovskite'],
            source=sources['murakami2004'],
            crystal_system='orthorhombic',
            space_group='Cmcm',
            lattice_a=2.45,
            lattice_b=8.21,
            lattice_c=6.27,
            volume=126.1,
            density=5.05,
            method='XRD',
            pressure=130.0,
            temperature=2500.0,
        )

        def create_eos(phase, source, eos_model, temperature, method, params, pv_points, ev_points=None):
            eos = EOSEntry.objects.create(
                phase=phase,
                source=source,
                eos_model=eos_model,
                temperature=temperature,
                pressure_min=min(p[0] for p in pv_points) if pv_points else None,
                pressure_max=max(p[0] for p in pv_points) if pv_points else None,
                volume_min=min(p[1] for p in pv_points) if pv_points else None,
                volume_max=max(p[1] for p in pv_points) if pv_points else None,
                method=method,
            )
            for name, value, unit, uncertainty in params:
                EOSParameter.objects.create(
                    eos_entry=eos, name=name, value=value, unit=unit, uncertainty=uncertainty
                )
            for p, v, t in pv_points:
                PVData.objects.create(
                    eos_entry=eos, pressure=p, volume=v, temperature=t,
                    pressure_unit='GPa', volume_unit='Å³',
                )
            if ev_points:
                for e, v in ev_points:
                    EVData.objects.create(
                        eos_entry=eos, energy=e, volume=v,
                        energy_unit='eV/atom', volume_unit='Å³',
                    )
            return eos

        # Bridgmanite EOS + PV/EV
        create_eos(
            phases['bridgmanite'], sources['dorfman2013'], 'Birch-Murnaghan', 300.0, 'DAC',
            params=[
                ('V0', 162.5, 'Å³', 0.5),
                ('K0', 260.0, 'GPa', 5.0),
                ('K0_prime', 4.0, '', 0.2),
            ],
            pv_points=[
                (0, 162.5, 300), (25, 155.0, 300), (50, 149.0, 300),
                (75, 144.0, 300), (100, 139.5, 300), (125, 135.5, 300),
            ],
            ev_points=[
                (-8.12, 162.5), (-8.08, 155.0), (-8.04, 149.0),
                (-8.00, 144.0), (-7.96, 139.5), (-7.92, 135.5),
            ],
        )

        # Ferropericlase EOS
        create_eos(
            phases['ferropericlase'], sources['lin2013'], 'Vinet', 300.0, 'DAC',
            params=[
                ('V0', 75.1, 'Å³', 0.3),
                ('K0', 185.0, 'GPa', 3.0),
                ('K0_prime', 4.2, '', 0.15),
            ],
            pv_points=[
                (0, 75.1, 300), (20, 71.5, 300), (40, 68.8, 300),
                (60, 66.5, 300), (80, 64.5, 300),
            ],
            ev_points=[
                (-6.85, 75.1), (-6.80, 71.5), (-6.75, 68.8), (-6.70, 66.5),
            ],
        )

        # Ca-perovskite EOS
        create_eos(
            phases['ca_perovskite'], sources['caracas2005'], 'Birch-Murnaghan', 0.0, 'DFT',
            params=[
                ('V0', 223.8, 'Å³', 1.0),
                ('K0', 310.0, 'GPa', 8.0),
                ('K0_prime', 3.5, '', 0.3),
            ],
            pv_points=[
                (0, 223.8, 0), (30, 210.0, 0), (60, 200.0, 0),
                (90, 192.0, 0), (120, 185.5, 0),
            ],
        )

        # Post-perovskite EOS (two temperature conditions for multi-series plots)
        create_eos(
            phases['post_perovskite'], sources['murakami2004'], 'Birch-Murnaghan', 2500.0, 'DAC',
            params=[
                ('V0', 126.1, 'Å³', 0.4),
                ('K0', 330.0, 'GPa', 6.0),
                ('K0_prime', 3.8, '', 0.2),
            ],
            pv_points=[
                (125, 126.1, 2500), (130, 124.5, 2500), (135, 123.0, 2500),
                (140, 121.6, 2500), (145, 120.2, 2500),
            ],
            ev_points=[
                (-8.20, 126.1), (-8.15, 124.5), (-8.10, 123.0), (-8.05, 121.6),
            ],
        )
        create_eos(
            phases['post_perovskite'], sources['ito2004'], 'Vinet', 300.0, 'DFT',
            params=[
                ('V0', 127.0, 'Å³', 0.5),
                ('K0', 325.0, 'GPa', 7.0),
                ('K0_prime', 3.6, '', 0.25),
            ],
            pv_points=[
                (125, 127.0, 300), (130, 125.3, 300), (135, 123.8, 300),
                (140, 122.4, 300),
            ],
        )

        # Elastic measurements
        ElasticMeasurement.objects.create(
            phase=phases['bridgmanite'],
            source=sources['ito2004'],
            pressure=25.0,
            temperature=300.0,
            density=4.35,
            bulk_modulus=260.0,
            shear_modulus=175.0,
            vp=11.2,
            vs=6.5,
            method='Brillouin spectroscopy',
        )
        ElasticMeasurement.objects.create(
            phase=phases['bridgmanite'],
            source=sources['dorfman2013'],
            pressure=120.0,
            temperature=2500.0,
            density=5.10,
            bulk_modulus=280.0,
            shear_modulus=150.0,
            vp=12.5,
            vs=6.8,
            method='Impulsive stimulated light scattering',
        )
        ElasticMeasurement.objects.create(
            phase=phases['ferropericlase'],
            source=sources['lin2013'],
            pressure=60.0,
            temperature=300.0,
            density=5.80,
            bulk_modulus=185.0,
            shear_modulus=95.0,
            vp=9.8,
            vs=5.2,
            method='Ultrasonic interferometry',
        )
        ElasticMeasurement.objects.create(
            phase=phases['ca_perovskite'],
            source=sources['caracas2005'],
            pressure=120.0,
            temperature=0.0,
            density=4.10,
            bulk_modulus=310.0,
            shear_modulus=120.0,
            vp=10.5,
            vs=5.8,
            method='DFT',
        )
        ElasticMeasurement.objects.create(
            phase=phases['post_perovskite'],
            source=sources['murakami2004'],
            pressure=130.0,
            temperature=2500.0,
            density=5.05,
            bulk_modulus=330.0,
            shear_modulus=140.0,
            vp=13.0,
            vs=7.0,
            method='XRD + elasticity model',
        )

        self.stdout.write(self.style.SUCCESS(
            f'Seed complete: {Phase.objects.count()} phases, '
            f'{Source.objects.count()} sources, '
            f'{EOSEntry.objects.count()} EOS entries.'
        ))
