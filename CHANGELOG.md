# Changelog
All notable changes to this project will be documented in this file.

## [Unreleased] - 2019-08-21
### Added
- New method in `Jones` class called `sph2lud3_basis` that converts spherical
  basis vectors to the Ludwig3 basis. It has an optional `alignment` rotation
  argument that allows the p/q directions of the dualpol antennas to be
  rotated w.r.t. to the reference spherical system.
- New class `LofarFeedJones` (subclass of `EJones`) to handle LOFAR
  specific details of its `EJones`. Basis of final Jones is now the unit
  vectors of the X/Y dipole vectors projected onto the plane transverse to the
  pointing direction, using a conversion to Ludwig3.
- `CHANGELOG.md` file.


## [0.3] - 2019-08-19
### Added
- New argument `--fmt` for `pointing_jones.py` script that controls print
  output. Can have values: `csv` (default) or `pac` (compatible)
- New argument `--no-pararot` and conversely `--pararot` (default) for
  `pointing_jones.py` script that either does not or does (resp.) apply the
  parallactic rotation.

### Changed
- Flipped X/Y signs in the LOFAR antenna build to station rotation.
  This results in a overall sign change of final Jones matrix (all components
  flip sign).


## [0.2] - 2019-04-14
### Added
- Flag in `PJones()` to turn off parallactic rotation.

### Changed
- Algorithm for parallactic rotation. Previously `PJones()` returned Jones
  in geocentric ITRF, and the ITRF2stn rotation was applied to the feed_pat
  (using its `rotateframe()`) in `EJones()`. Since this calculation was done in
  ITRF, it was difficult to access the parallactic rotation which is normally
  viewed as rotation from celestial frame to topocentric frame.
  Now `PJones` returns Jones in local, geocentric STN frame (topocentric) using
  the ITRF2stn rotation and the `EJones` is also computed in the STN frame.
- Start using C09 convention consistently for spherical basis vectors
  [Carozzi2009](https://doi.org/10.1111/j.1365-2966.2009.14642.x). This implied
  two major changes: the `DualPolFieldPointSrc` class is now defined in the C09
  basis and converts the Jones components accordingly, rather than as
  previously, keep the IAU components and convert the basis C09 to IAU.
- Mapping of the Jones columns (`AntPat` sph basis comps.) returned from
  `dualPolElem.getJonesAlong()` in `EJones()` to corresponding C09 sph basis
  components, rather than identity mapping.


## [0.1] - 2019-04-11
### Added
- Basic framework for project, consisting of a `rime` package that implements
  generic Radio Interferometric Measurement Equations, and a `telescopes`
  package which contains runtime pluggable modules for specific telescopes.
- `LOFAR` module under `telescopes`.
- print output from `pointing_jones.py` is now CSV.


## [0.0] - 2016-03-26
### Added
- Start using git as VCS for project.