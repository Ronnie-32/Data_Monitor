"""Timetable-scheme service facade kept within the CourseService boundary."""

from deskboard.services.course_service import CourseService


class TimetableSchemeService(CourseService):
    """Named facade for callers that manage only timetable schemes."""

    create_scheme = CourseService.create_timetable_scheme
    get_scheme = CourseService.get_timetable_scheme
    require_scheme = CourseService.require_timetable_scheme
    list_schemes = CourseService.list_timetable_schemes
    save_scheme = CourseService.save_timetable_scheme
    update_scheme = CourseService.save_timetable_scheme
    duplicate_scheme = CourseService.duplicate_timetable_scheme
    rename_scheme = CourseService.rename_timetable_scheme
    delete_scheme = CourseService.delete_timetable_scheme
    bind_scheme = CourseService.bind_semester_timetable_scheme
