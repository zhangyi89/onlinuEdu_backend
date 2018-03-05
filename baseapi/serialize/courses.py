from rest_framework import serializers
from ..models import *


class CourseCapterCharField(serializers.CharField):

    def to_representation(self, instance):
        # instance是QuerySet对象
        data_list = []
        for row in instance:
            data_list.append({'id': row.id, 'price': row.price, 'valid_period': row.get_valid_period_display()})
        return data_list


class QuestionCharField(serializers.CharField):

    def to_representation(self, instance):
        # instance是QuerySet对象
        data_list = []
        for row in instance:
            data_list.append({'question': row.question, 'answer': row.answer})
        return data_list


class CourseSerializer(serializers.ModelSerializer):
    level = serializers.SerializerMethodField()  # 获取一个对象
    course_type = serializers.SerializerMethodField()
    price_policy = CourseCapterCharField(source="price_policy.all")
    # price_policy = serializers.CharField(source="price_policy.all")

    coursedetail = serializers.SerializerMethodField()

    # 推荐课程
    recommend_courses = serializers.SerializerMethodField()

    # 讲师
    teachers = serializers.SerializerMethodField()

    # 常见问题
    questions = QuestionCharField(source="questions.all")

    class Meta:
        model = Course
        fields = "__all__"
        depth = 2

    def get_level(self, obj):
        # 某个对象的钩子函数
        return obj.get_level_display()

    def get_course_type(self, obj):
        return obj.get_course_type_display()

    def get_coursedetail(self, obj):
        return {'hours': obj.coursedetail.hours, 'why_study': obj.coursedetail.why_study,
                'what_to_study_brief': obj.coursedetail.what_to_study_brief,
                'career_improvement': obj.coursedetail.career_improvement,
                'prerequisite': obj.coursedetail.prerequisite}

    def get_recommend_courses(self, obj):
        recommend_courses_list = obj.coursedetail.recommend_courses.all()
        data_list = []
        for item in recommend_courses_list:
            data_list.append({'name': item.name, 'id': item.id})
        return data_list

    def get_teachers(self, obj):
        recommend_courses_list = obj.coursedetail.teachers.all()
        data_list = []
        for item in recommend_courses_list:
            data_list.append({'name': item.name, 'role': item.get_role_display(),
                              'image': item.image, 'signature': item.signature,'brief': item.brief})
        return data_list


class CourseDetailCharField(serializers.CharField):

    def to_representation(self, instance):
        # instance是QuerySet对象
        data_list = []
        for row in instance:
            for item in row.course.all():
                data_list.append({'capter': row.chapter, 'sections': item.name})
        return data_list


class CourseDetailSerializer(serializers.ModelSerializer):

    level = serializers.SerializerMethodField()
    # course = serializers.SerializerMethodField()
    # 通过自定义的MyCharField中的to_representation处理多对多字段的QuerySet对象
    # course_captal = CourseCapterCharField(source="course.coursechapters")

    class Meta:
        model = CourseDetail
        fields = "__all__"
        depth = 4

    def get_level(self, obj):
        # 该方法会在返回的json数据中添加一条数据,如果get_后面的名字和原始返回的数据重复则会覆盖原始的字段，如果不存在则会添加。
        # {'level': 'obj.course.get_level_display()',........}
        # {'id': 1, 'level': '中级',
        return obj.course.get_level_display()

    # def get_course(self, obj):
    #     # 覆盖了之前的course
    #     data = {}
    #     data['level'] = obj.course.get_level_display()
    #     return data


