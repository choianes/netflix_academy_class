try:
    import maya.cmds as cmds # Maya 명령어 모듈 가져오기
    import maya.mel as mel   # Maya MEL 스크립트 모듈 가져오기
except:
    pass
import os # 운영체제 명령어 모듈
import json # JSON 파일 처리 모듈
import subprocess  # 외부 프로세스 실행을 위한 모듈
import datetime # 날짜 및 시간 모듈
import ffmpeg # 동영상 처리를 위한 FFmpeg 모듈
import glob # 파일 및 폴더 검색 모듈
import re # 정규 표현식 모듈

# Maya API 작업을 수행하는 클래스를 정의
class MayaAPI():
    def __init__(self):
        pass

    def get_file_name(self):
        """현재 열려있는 마야 파일 이름 가져오는 메서드"""
        filepath = cmds.file(q=True, sn=True) # 현재 파일 경로를 얻음
        filename = os.path.basename(filepath) # 파일 이름만 추출
        return filename

    def get_selected_objects(self):
        """선택한 오브젝트 리스트 가져오는 메서드"""
        return cmds.ls(sl=True) # 선택된 오브젝트 리스트 반환
    
    def save_file(self, path):
        """ Maya 파일을 지정된 경로에 저장하는 함수""" 
        cmds.file(rename=path) # 파일 이름과 경로 설정
        cmds.file(save=True, type='mayaBinary') # Maya Binary 형식으로 저장
        print(f"Model saved as Maya Binary file to: {path}")  # 저장 완료 메시지 출력


    
########################### Modeling #####################################3

     # 모델링 작업을 퍼블리시하기 위한 기본 설정을 수행하는 함수
    @staticmethod
    def modeling_publish_set(self):
        # 1. 선택한 오브젝트들의 스케일 고정 (Freeze Transformations)
        selected_objects = cmds.ls(selection=True)
        if selected_objects:
            cmds.makeIdentity(selected_objects, apply=True, scale=True) # 스케일 고정
            print("선택된 오브젝트의 Scale이 1로 고정되었습니다.")
        else:
            print("선택된 오브젝트가 없습니다. Scale 고정 작업을 건너뜁니다.")

        # 2. 히스토리 삭제 (Delete History)
        if selected_objects:
            cmds.delete(selected_objects, constructionHistory=True) # 히스토리 삭제
            print("선택된 오브젝트의 히스토리가 삭제되었습니다.")
        else:
            print("선택된 오브젝트가 없습니다. 히스토리 삭제 작업을 건너뜁니다.")

        # 3. 사용되지 않는 쉐이더 삭제 (Delete Unused Shaders)
        all_shaders = cmds.ls(materials=True)
        used_shaders = cmds.ls(cmds.listConnections(cmds.ls(geometry=True)), materials=True)

        unused_shaders = list(set(all_shaders) - set(used_shaders)) # 사용되지 않은 쉐이더 찾기

        if unused_shaders:
            cmds.delete(unused_shaders) # 미사용 쉐이더 삭제
            print(f"{len(unused_shaders)}개의 필요없는 쉐이더가 삭제되었습니다.")
        else:
            print("삭제할 필요없는 쉐이더가 없습니다.")
    
    def set_single_renderable_camera(self, camera_name):
        """
        지정된 카메라만 렌더러블 상태로 유지하고, 다른 모든 카메라는 비활성화합니다.
        """
        all_cameras = cmds.ls(type='camera') # 씬에 있는 모든 카메라 찾기
        for cam in all_cameras:
            cmds.setAttr(f"{cam}.renderable", cam == camera_name) # 지정된 카메라만 렌더러블 상태로 설정

    def render_turntable(self, output_path_template, start_frame=1001, end_frame=1096, width=1920, height=1080, distance = 5, department=None):
        """턴테이블 애니메이션을 위한 설정"""

        start_frame = int(cmds.playbackOptions(query=True, minTime=True))  # 시작 프레임 읽기
        end_frame = int(cmds.playbackOptions(query=True, maxTime=True))    # 끝 프레임 읽기
        
        ext = os.path.splitext(output_path_template)[1]  # 파일 확장자 추출
        output_path = output_path_template.replace('.####.exr', '')  # 경로 템플릿에서 확장자 제거
        print ("=============", output_path)
        self.set_image_format(ext) # 이미지 형식 설정
        cmds.setAttr("defaultResolution.width", width) # 렌더 해상도 너비 설정
        cmds.setAttr("defaultResolution.height", height) # 렌더 해상도 높이 설정

        # dome light 만들기 ( Arnold의 돔라이트가 존재하지 않으면 생성)
        dome_lights = cmds.ls(type='aiSkyDomeLight')  # Arnold 돔라이트 확인
        if dome_lights:
            print("Dome light already exists.")
        else:
            dome_light = cmds.shadingNode("aiSkyDomeLight", asLight=True, name="domedome")

        # 특정 부서가 'LKD'일 경우, HDRI 파일을 돔라이트에 연결
        if department == 'LKD':
            print ("it's shader time")
            hdri_path = "/home/rapa/baked/show/baked/ONSET/rosendal_plains_2_2k.exr"
            file_node = cmds.shadingNode('file', asTexture=True)

            # 파일 텍스처의 경로 설정
            cmds.setAttr(f"{file_node}.fileTextureName", hdri_path, type="string") # 텍스처 파일 경로 설정
            # DomeLight의 color 속성과 파일 텍스처의 outColor 속성 연결
            cmds.connectAttr(f"{file_node}.outColor", f"{dome_light}.color", force=True)

        camera_transform, camera_shape = cmds.camera(name='turntable_camrea_pub') # 카메라 생성
        # cmds.viewFit(camera_transform)  # 자동으로 카메라 위치 세팅
        cmds.setAttr(camera_transform + ".translateZ", 8)  # 카메라 거리를 설정
        cmds.setAttr(camera_transform + ".translateY", 2)  # 카메라 거리를 설정
        # 카메라 그룹 생성 및 그룹에 카메라 추가
        turntable_grp = cmds.group(empty=True, name='turntable_camera_grp')
        cmds.parent(camera_transform, turntable_grp)

        # 애니메이션 키프레임 설정 (카메라 회전)
        start_frame = int(cmds.playbackOptions(query=True, minTime=True))  # 시작 프레임 읽기
        end_frame = int(cmds.playbackOptions(query=True, maxTime=True))    # 끝 프레임 읽기
        cmds.setKeyframe(turntable_grp, attribute="rotateY", time=start_frame, value=0)
        cmds.setKeyframe(turntable_grp, attribute="rotateY", time=end_frame, value=360)
        cmds.setAttr(f"{camera_shape}.renderable", True)

        # 키프레임을 선형으로 설정
        cmds.keyTangent(turntable_grp, attribute="rotateY", inTangentType="linear", outTangentType="linear")

        # 턴테이블 - 배치 렌더링 수행 (Arnold 렌더러 사용)
        cmds.setAttr("defaultRenderGlobals.imageFilePrefix", output_path, type="string")
        output_path = output_path.replace(".####.", ".%04d.")
        cmds.arnoldRender(batch=True)

        print ("exr 을 jpg로 바꿔주기")
        return output_path_template


####################### Animation #################################################33

    def export_alemibc(self, abc_cache_path, asset):
        """
        알렘빅이 저장될 경로를(디렉토리) 이용
        """
        print ("*******************")
        print (asset, abc_cache_path)
        print ("*******************")

        start_frame = int(cmds.playbackOptions(query=True, min=True)) - 10 # 시작 프레임
        last_frame = int(cmds.playbackOptions(query=True, max=True)) + 10 # 끝 프레임

        alembic_args = ["-renderableOnly", "-writeFaceSets", "-uvWrite", "-worldSpace", "-eulerFilter"]

        alembic_args.append(f"-fr {start_frame} {last_frame}") # 프레임 범위 설정
        alembic_args.append(f"-file '{abc_cache_path}'")  # 저장 경로 설정
        alembic_args.append(f"-root {asset}") # 에셋 설정
        abc_export_cmd = 'AbcExport -j "%s"' % " ".join(alembic_args)
        mel.eval(abc_export_cmd) # MEL 명령으로 Alembic 내보내기 실행
    

################### 플레이블라스트, 렌더, ffmpeg ########################################
    
    def make_playblast(self, image_path):
        """
        마야의 플레이 블라스트 기능을 이용해서 뷰포트를 이미지로 렌더링하고,
        슬레이트 정보를 삽입하여 동영상을 인코딩한다.
        """
        # 이미지 파일의 경로에서 확장자를 분리하고 저장 경로 설정
        proxy_path = ''.join(image_path.split('.')[0])
        _, proxy_format = os.path.splitext(image_path)
        proxy_format = proxy_format[1:]
        
        print (f"image path {image_path}")
        print (f"proxy path :{proxy_path}")
        print (f"proxy format :{proxy_format}")

        # 마야 타임라인에서 시작 프레임과 끝 프레임을 가져옴
        start_frame = int(cmds.playbackOptions(query=True, min=True))
        last_frame = int(cmds.playbackOptions(query=True, max=True))

        # 렌더 해상도 설정 (1920x1080)
        render_width = 1920
        render_height = 1080

        # 마야의 플레이블라스트(뷰포트 이미지를 파일로 저장하는 기능)를 사용하여 이미지 저장
        cmds.playblast(filename=proxy_path, format='image', compression=proxy_format,
                        startTime=start_frame, endTime=last_frame, forceOverwrite=True,
                        widthHeight=(render_width, render_height), percent=100,
                        showOrnaments=True, framePadding=4, quality=100, viewer=False)
        
        # 시작 프레임과 마지막 프레임 반환
        return start_frame, last_frame
    
    def make_ffmpeg(self, start_frame, last_frame, input_path, output_path, project_name):
        ## 플레이블라스트로 렌더링한 이미지를 FFMPEG 라이브러리를 이용해서 동영상을 인코딩한다.

        # 기본 설정
        first = 1001
        frame_rate = 24
        # 사운드가 있는 경우 23.976 으로 합니다.
        # 이 경우 ffmpeg에 사운드 파일을 추가하는 설정이 필요합니다.
        ffmpeg = "ffmpeg"
        slate_size = 60 # 슬레이트의 높이
        font_path = "/home/rapa/baked/toolkit/config/core/content/font/Courier_New.ttf" # 슬레이트에 사용할 폰트
        start_frame, last_frame = self.get_frame_number(input_path)
        frame_count = int(last_frame) - int(start_frame) # 총 프레임 수 계산
        font_size = 40
        text_x_padding = 10
        text_y_padding = 20

        # 슬레이트의 각 위치에 들어갈 텍스트 설정
        top_left, _ = os.path.splitext(os.path.basename(output_path))  # 상단 왼쪽 텍스트: 출력 파일 이름
        top_center = project_name  # 상단 중앙 텍스트: 프로젝트 이름
        top_right = datetime.date.today().strftime("%Y/%m/%d")  # 상단 오른쪽 텍스트: 오늘 날짜
        bot_left = "1920x1080"  # 하단 왼쪽 텍스트: 해상도
        bot_center = ""  # 하단 중앙은 빈칸
        frame_cmd = "'Frame \: %{eif\:n+"  # 프레임 번호 표시
        frame_cmd += "%s\:d}' (%s)"  % (start_frame, frame_count+1)
        bot_right = frame_cmd  # 하단 오른쪽에 프레임 정보 추가

        try:
            input_path = input_path.replace(".####.", ".%04d.")  # 파일 경로에서 프레임 번호를 변환
        except:
            pass

        if last_frame == 1:
            return # 렌더링할 프레임이 없으면 종료
        
        # FFMPEG 명령어를 구성해 동영상 인코딩 수행
        cmd = '%s -framerate %s -y -start_number %s ' % (ffmpeg, frame_rate, start_frame)
        cmd += '-i %s' % (input_path)
        cmd += ' -vf "drawbox=y=0 :color=black :width=iw: height=%s :t=fill, ' % (slate_size)
        cmd += 'drawbox=y=ih-%s :color=black :width=iw: height=%s :t=fill, ' % (slate_size, slate_size)
        cmd += 'drawtext=fontfile=%s :fontsize=%s :fontcolor=white@0.7 :text=%s :x=%s :y=%s,' % (font_path, font_size, top_left, text_x_padding, text_y_padding)
        cmd += 'drawtext=fontfile=%s :fontsize=%s :fontcolor=white@0.7 :text=%s :x=(w-text_w)/2 :y=%s,' % (font_path, font_size, top_center, text_y_padding)
        cmd += 'drawtext=fontfile=%s :fontsize=%s :fontcolor=white@0.7 :text=%s :x=w-tw-%s :y=%s,' % (font_path, font_size, top_right, text_x_padding, text_y_padding)
        cmd += 'drawtext=fontfile=%s :fontsize=%s :fontcolor=white@0.7 :text=%s :x=%s :y=h-th-%s,' % (font_path, font_size, bot_left, text_x_padding, text_y_padding)
        cmd += 'drawtext=fontfile=%s :fontsize=%s :fontcolor=white@0.7 :text=%s :x=(w-text_w)/2 :y=h-th-%s,' % (font_path, font_size, bot_center, text_y_padding)
        cmd += 'drawtext=fontfile=%s :fontsize=%s :fontcolor=white@0.7 :text=%s :x=w-tw-%s :y=h-th-%s' % (font_path, font_size, bot_right, text_x_padding, text_y_padding)
        cmd += '"'
        cmd += ' -c:v prores_ks -profile:v 3 -colorspace bt709 %s' % output_path
        os.system(cmd) # 명령어 실행
        return output_path
    
    def get_frame_number(self, path):
        """
        파일 경로에서 프레임 번호를 추출하여 시작과 끝 프레임 번호를 반환한다.
        """
        print("++++++++++++++++++++++++++++++++++++++")
        dir_path = os.path.dirname(path)  # 경로에서 디렉토리 경로 추출
        files = glob.glob(f"{dir_path}/*")  # 디렉토리 내 모든 파일 리스트
        files = sorted(files)


        print("----------------------------------------------------------")
        print(files)
        for index, file in enumerate(files):
            p = re.compile("[.]\d{4}[.]")  # 파일 이름에서 4자리 숫자를 찾는 정규 표현식
            frame = p.search(file)
            if frame:
                frame = frame.group()[1:5]  # 프레임 번호 추출
                files[index] = frame
            else:
                files.remove(file)
                
        p_start = min(files)  # 가장 작은 프레임 번호
        p_last = max(files)  # 가장 큰 프레임 번호
        
        print(p_start, p_last)      
        return p_start, p_last  # 시작과 끝 프레임 번호 반환

################################## 매치무브 ###################################3

    def get_undistortion_size(self):
        """
        마야에서 설정된 렌더 해상도를 가져오는 함수.
        카메라 렌즈 왜곡 제거에 필요한 이미지 크기를 반환합니다.
        """
        width = cmds.getAttr('defualtResolution.width')  # 렌더 해상도의 가로 크기
        height = cmds.getAttr('defaultResolution.height')  # 렌더 해상도의 세로 크기

        return width, height  # 가로 및 세로 크기 반환
    
##################################################################################33

    def render_to_multiple_formats(self, output_path, width=1920, height=1080):
        """
        여러 이미지 형식으로 렌더링하는 함수. 예를 들어 jpg, png, exr 형식으로 출력.
        지정한 해상도(width x height)로 렌더링을 수행하고, 출력 경로를 설정합니다.
        """
        
        # 렌더링 해상도를 설정합니다.
        cmds.setAttr("defaultResolution.width", width)
        cmds.setAttr("defaultResolution.height", height)
        
        # 현재 뷰포트에 있는 카메라를 가져옵니다.
        current_camera = cmds.modelPanel(cmds.getPanel(withFocus=True), q=True, camera=True)
        
        # 이미지 형식을 설정한 후, 렌더링을 수행합니다.
        ext = os.path.splitext(output_path)[1]  # 출력 경로에서 파일 확장자를 가져옴
        self.set_image_format(ext)  # 확장자에 맞는 이미지 형식 설정
        cmds.render(current_camera, x=width, y=height, f=output_path)  # 렌더링 실행

    def set_image_format(self, format_name):
        """
        이미지 형식을 설정하는 함수.
        주어진 확장자에 따라 렌더링할 이미지 형식을 설정합니다.
        예: .jpg, .png, .exr 등
        """
        format_dict = {
            ".jpg": 8,    # JPEG 형식
            ".jpeg": 8,   # JPEG 형식
            ".exr": 51,   # EXR 형식
            ".png": 32,   # PNG 형식
            ".tiff": 3,   # TIFF 형식
            ".tif": 3,    # TIFF 형식
        }
        
         # 확장자가 사전에 있는 경우 해당 형식으로 설정
        if format_name.lower() in format_dict:
            cmds.setAttr("defaultRenderGlobals.imageFormat", format_dict[format_name.lower()])
        else:
            raise ValueError(f"지원되지 않는 이미지 형식: {format_name}")  # 지원되지 않는 형식일 때 에러 발생

    def render_file(self, outpath):
        """
        주어진 경로(outpath)로 마야 씬을 렌더링하는 함수.
        선택한 카메라로 렌더링을 수행하고, 이미지 파일을 저장합니다.
        """
        output_dir = f"{os.path.dirname(outpath)}/"  # 출력 경로 설정
        print("렌더중", outpath, output_dir)
        
        # 사용할 카메라 설정 (aniCam 또는 mmCam 중 하나 선택)
        camera_name = None
        if cmds.objExists("aniCam"):
            camera_name = "aniCam"
        elif cmds.objExists("mmCam"):
            camera_name = "mmCam"
        
        # 둘 중 하나의 카메라가 없으면 에러 메시지 출력
        if not camera_name:
            print("Error: Neither 'aniCam' nor 'mmCam' exists in the scene.")
            return
        
        # 선택한 카메라를 렌더러블 상태로 설정
        self.set_single_renderable_camera(camera_name)


        # 렌더링 파일의 이름 및 프레임 설정
        filename_template = "<Scene>"
        cmds.setAttr("defaultRenderGlobals.imageFilePrefix", output_dir + filename_template, type="string")
        cmds.setAttr("defaultRenderGlobals.extensionPadding", 4)  # 파일 이름에 들어가는 프레임 숫자 자릿수
        cmds.setAttr("defaultRenderGlobals.animation", 1)  # 애니메이션 렌더링 활성화
        cmds.setAttr("defaultRenderGlobals.putFrameBeforeExt", 1)  # 프레임 번호를 확장자 앞에 배치
        cmds.arnoldRender(batch=True)  # Arnold 렌더러로 배치 렌더링 실행
        thumbnail_path = self.convert_exr_into_jpg(outpath)  # 렌더된 EXR 파일을 JPG로 변환
        return thumbnail_path

        
    def convert_exr_into_jpg(self, input_file):
        """
        EXR 파일을 JPG 형식으로 변환하는 함수.
        FFMPEG을 이용하여 EXR 파일을 고품질 JPG로 변환합니다.
        """
        output_file = input_file.replace(".####.exr", ".jpg")  # EXR 확장자를 JPG로 변경
        files = glob.glob(f"{os.path.dirname(output_file)}/*")  # 파일 목록 가져오기
        input_file = max(files, key=os.path.getmtime)  # 가장 최근에 수정된 파일 선택
        print("변환 중", input_file, output_file)
        
        try:
            # FFMPEG 명령어를 사용해 EXR 파일을 JPG로 변환
            command = [
                'ffmpeg',
                '-i', input_file,   # 입력 파일 (EXR)
                '-q:v', "2",        # 품질 설정 (2가 높은 품질)
                output_file         # 출력 파일 (JPG)
            ]
            subprocess.run(command, check=True)  # FFMPEG 명령 실행
            print(f"변환 성공: {output_file}")
    
        except subprocess.CalledProcessError as e:
            print(f"변환 실패: {e}")
        
        return output_file  # 변환된 JPG 파일 경로 반환        

###### 쉐이더 ###################################################################

    def collect_shader_assignments(self):
        """
        Maya 씬에서 각 오브젝트에 할당된 셰이더(Shader) 정보를 수집하는 함수.
        셰이더와 해당 오브젝트들의 매핑 관계를 딕셔너리로 반환합니다.
        """
        shader_dictionary = {}
        shading_groups = cmds.ls(type="shadingEngine")  # 씬에 있는 모든 셰이딩 그룹 가져오기
        for shading_group in shading_groups:
            shader = cmds.ls(cmds.listConnections(shading_group + ".surfaceShader"), materials=True)  # 셰이더 연결 정보 가져오기
            if not shader:
                continue  # 셰이더가 없으면 다음으로 넘어감
            objects = cmds.sets(shading_group, q=True)  # 셰이더가 적용된 오브젝트들 가져오기
            shader_name = shader[0]
            if objects:
                if shader_name not in shader_dictionary:
                    shader_dictionary[shader_name] = []
                shader_dictionary[shader_name].extend(objects)  # 셰이더와 오브젝트들을 딕셔너리에 저장
        return shader_dictionary

    def export_shader(self, ma_file_path, json_file_path):
        """
        Maya 씬에서 각 오브젝트에 할당된 셰이더들을 .ma 파일로 익스포트하고,
        그 정보를 JSON 파일로 저장하는 함수입니다.
        """
        shader_dictionary = self.collect_shader_assignments()  # 셰이더와 오브젝트 정보를 수집
        ma_file_dir_path = os.path.dirname(ma_file_path)  # .ma 파일 저장 경로
        json_file_name = os.path.basename(ma_file_path).replace(".ma", ".json")  # .ma 파일 이름을 .json으로 변경
        json_file_path = f"{ma_file_dir_path}/{json_file_name}"
        print(json_file_path)

        # 모든 셰이더를 선택한 후 .ma 파일로 익스포트
        for shader, _ in shader_dictionary.items():
            cmds.select(shader, add=True)    
        
        cmds.file(ma_file_path, exportSelected=True, type="mayaAscii")  # 선택된 셰이더를 .ma 파일로 익스포트
        with open(json_file_path, 'w') as f:
            json.dump(shader_dictionary, f)  # 셰이더 정보를 JSON 파일로 저장

        cmds.select(clear=True)  # 선택 초기화
        
        # 결과 출력
        print(f"Shaders exported to: {ma_file_path}")  # .ma 파일 경로 출력
        print(f"Shader assignment data exported to: {json_file_path}")  # JSON 파일 경로 출력
        print("Shader Dictionary:")
        for shader, objects in shader_dictionary.items():
            print(f"  Shader: {shader} -> Objects: {objects}")  # 각 셰이더와 해당 오브젝트 출력

        return json_file_name, json_file_path  # JSON 파일 이름과 경로 반환

    def get_custom_shader_list(self):
        """
        Maya 씬에서 기본 쉐이더를 제외한 사용자 정의 쉐이더 목록을 가져옵니다.
        
        Returns:
        list: 사용자 정의 쉐이더 이름들의 리스트
        """
        # 기본 쉐이더 목록 (제외할 쉐이더)
        default_shaders = {'lambert1', 'particleCloud1', 'shaderGlow1'}

        # 씬에 있는 모든 쉐이더를 가져옵니다.
        shaders = cmds.ls(materials=True)

        # 사용자 정의 쉐이더만 필터링
        custom_shaders = [shader for shader in shaders if shader not in default_shaders]

        # 사용자 정의 쉐이더 목록 출력
        print("Custom Shader List:", custom_shaders)
        
        return custom_shaders # 사용자 정의 쉐이더 목록 반환
    
    def get_texture_list(self):
        """
        Maya 씬에서 사용된 텍스처 파일들의 이름을 가져옵니다.
        
        Returns:
        list: 텍스처 파일 이름들의 리스트
        """
        textures = []
        file_nodes = cmds.ls(type="file")
        for node in file_nodes:
            # 텍스처 파일 경로를 가져옴
            file_path = cmds.getAttr(f"{node}.fileTextureName")
            # 파일 이름만 추출
            file_name = os.path.basename(file_path)
            textures.append(file_name)
        
        textures = textures.remove("")
        print("텍스처 파일 이름 목록:", textures)
        return textures
    
    def render_exr_sequence(self, output_path):
        """
        'anicam' 또는 'mmcam' 카메라를 사용하여 여러 프레임을 .exr 형식으로 렌더링합니다.
        
        """
        # 'anicam' 또는 'mmcam' 카메라를 사용 (우선 'anicam', 없으면 'mmcam')
        camera_name = None
        if cmds.objExists("aniCam"):
            camera_name = "aniCam"
        elif cmds.objExists("mmCam"):
            camera_name = "mmCam"
        
        if not camera_name:
            print("Error: Neither 'aniCam' nor 'mmCam' exists in the scene.")
            return
        
        print(f"Using camera: {camera_name}")
        
        # 지정된 카메라만 렌더러블 상태로 유지
        self.set_single_renderable_camera(camera_name)

        # 렌더링 시작 및 끝 프레임 가져오기
        start_frame = cmds.playbackOptions(q=True, min=True)
        last_frame = cmds.playbackOptions(q=True, max=True)

        
        # 렌더 설정: EXR 형식, Arnold 렌더러 사용
        cmds.setAttr("defaultRenderGlobals.imageFormat", 51)  # 51: OpenEXR 형식
        cmds.setAttr("defaultRenderGlobals.imfkey", "exr", type="string")
        cmds.setAttr("defaultRenderGlobals.currentRenderer", "arnold", type="string")
        
        # 프레임 범위에 따라 렌더링 수행
        for frame in range(start_frame, last_frame + 1):
            cmds.currentTime(frame)  # 현재 프레임 설정
            cmds.setAttr("defaultRenderGlobals.imageFilePrefix", output_path, type="string")
            cmds.arnoldRender(cam=camera_name, width=1920, height=1080)
            print(f"Rendered frame {frame} saved as {output_path}")

    def get_texture_list(self):
        """
        Maya 씬에서 사용된 텍스처 파일들의 이름을 가져옵니다.
        
        Returns:
        list: 텍스처 파일 이름들의 리스트
        """
        textures = []
        file_nodes = cmds.ls(type="file")
        for node in file_nodes:
            # 텍스처 파일 경로를 가져옴
            file_path = cmds.getAttr(f"{node}.fileTextureName")
            # 파일 이름만 추출
            file_name = os.path.basename(file_path)
            textures.append(file_name)
        
        print("텍스처 파일 이름 목록:", textures)
        return textures

    def publish_shader(self, output_path, shaders=None):
        """
        선택한 쉐이더를 .ma 파일로 퍼블리시하는 함수.

        Args:
        output_path (str): 퍼블리시할 .ma 파일의 경로
        shaders (list): 퍼블리시할 쉐이더 목록 (None이면 현재 선택된 쉐이더 사용)
        """
        # 퍼블리시할 쉐이더가 지정되지 않으면 현재 선택된 쉐이더 사용
        if shaders is None:
            shaders = cmds.ls(sl=True, dag=True, s=True)

        # 쉐이더 목록을 선택하여 퍼블리시
        if shaders:
            cmds.select(shaders)
            cmds.file(output_path, type='mayaAscii', exportSelected=True, force=True)
            print(f"Shaders exported to: {output_path}")
        else:
            print("선택된 쉐이더가 없습니다. 퍼블리시할 수 없습니다.")


    def publish_shader(output_path, shaders=None):
        """
        쉐이더를 .ma 파일로 퍼블리시하는 함수.

        :param output_path: 퍼블리시할 .ma 파일의 경로
        :param shaders: 퍼블리시할 쉐이의 목록 (None이면 현재 선택된 쉐이더 사용)
        """
        # 만약 쉐이더가 None이면 현재 선택된 쉐이더 사용
        if shaders is None:
            shaders = cmds.ls(sl=True, dag=True, s=True)

        # 쉐이더 목록을 선택하여 퍼블리시
        if shaders:
            cmds.select(shaders)
            cmds.file(output_path, type='mayaAscii', exportSelected=True, force=True)
        else:
            print("선택된 쉐이더가 없습니다. 퍼블리시할 수 없습니다.")

        def get_custom_shader_list():
            # 기본 쉐이더 목록 정의
            default_shaders = ['lambert1', 'particleCloud1', 'shaderGlow1', 'initialShadingGroup', 'initialParticleSE']
            
            # 씬에서 모든 쉐이더 가져오기
            all_shaders = cmds.ls(materials=True)
            
            # 기본 쉐이더를 제외한 사용자 정의 쉐이더만 필터링
            custom_shaders = [shader for shader in all_shaders if shader not in default_shaders]
            
            return custom_shaders


    def publish_shaders_as_ma(shader_list, output_path):
        """
        선택된 쉐이더들을 .ma 파일로 저장하는 함수.
        
        Args:
        shader_list (list): 퍼블리시할 쉐이더들의 목록.
        output_path (str): 저장할 .ma 파일의 경로.
        """
        # 새로운 씬을 생성하여 쉐이더만 내보내기 위해 기존 씬을 클리어
        cmds.file(new=True, force=True)

        # 쉐이더를 선택하여 씬에 가져오기
        for shader in shader_list:
            shading_groups = cmds.listConnections(shader, type='shadingEngine')
            if shading_groups:
                for sg in shading_groups:
                    cmds.select(sg, add=True)

        # .ma 파일 형식으로 저장
        cmds.file(rename=output_path)
        cmds.file(save=True, type='mayaAscii')

        print(f"Shaders saved as Maya ASCII (.ma) file to: {output_path}")

    def export_camera_cache(self, output_path, camera_name):
        """
        'anicam' 또는 'mmcam'이라는 이름의 카메라 애니메이션을 Alembic 캐시 파일로 내보내고,
        지정된 경로에 저장합니다. 'anicam'이 존재하면 이 카메라를 사용하고,
        존재하지 않으면 'mmcam'을 사용합니다.
        
        """
        
        # 우선적으로 'anicam' 카메라를 찾고, 없으면 'mmcam'을 찾음
        camera_name = None
        if 'aniCam'in camera_name:
            camera = camera_name
        elif "mmCam" in camera_name:
            camera = camera_name
        
        if not camera:
            print("Error: Neither 'anicam' nor 'mmcam' exists in the scene.")
            return
        
        # Alembic 내보내기 함수 호출
        self.export_alemibc(output_path, camera)

    def _get_lighting_layers(self):
        """
        씬에서 모든 렌더 레이어 목록을 가져오는 함수.
        
        """
        all_layers = cmds.ls(type="renderLayer")
        return all_layers
        
    def render_all_layers_to_exr(self, layer, publish_dict):
        """
        모든 렌더 레이어를 EXR 형식으로 렌더링하고, 지정된 경로에 저장하는 함수.
        
        """

        camera_name = None
        if cmds.objExists("aniCam"):
            camera_name = "aniCam"
        elif cmds.objExists("mmCam"):
            camera_name = "mmCam"
        
        if not camera_name:
            print("Error: Neither 'aniCam' nor 'mmCam' exists in the scene.")
            return
        
        print(f"Using camera: {camera_name}")
        
        # 지정된 카메라만 렌더러블 상태로 유지
        self.set_single_renderable_camera(camera_name)
        path = publish_dict[layer]["path"]
        output_dir = '/'.join(path.split('/')[:-1])

        # 렌더 레이어 변경
        cmds.editRenderLayerGlobals(currentRenderLayer=layer)

        
        # 파일 이름 접두사 설정
        file_prefix = f"{output_dir}/{layer}/{layer}"
        cmds.setAttr("defaultRenderGlobals.imageFilePrefix", file_prefix, type="string")
        print (publish_dict)
        
        # 배치 렌더링 수행
        cmds.arnoldRender(batch=True)
        print(f"{layer} 레이어의 EXR 렌더링이 {file_prefix}.####.exr 경로에 완료되었습니다.")

        # 경로 업데이트
        publish_dict[layer]["path"] = f"{file_prefix}.####.exr"
        return publish_dict
    
    def _render_lighting_layers(self, render_path):
        """
        주어진 경로에 있는 모든 렌더 레이어를 렌더링하는 함수.
        
        Args:
        render_path (str): 렌더링된 이미지가 저장될 경로.
        """
        print ("@@", render_path)
        dir_path = '/'.join(render_path.split('/')[:-1])

        # 파일 경로설정
        cmds.setAttr("defaultRenderGlobals.imageFilePrefix", dir_path, type="string")

        # 씬에 있는 모든 렌더 레이어 선택 후 렌더링 수행
        all_layers = cmds.ls(type="renderLayer")
        for layer in all_layers:
            # 렌더 레이어 변경
            cmds.editRenderLayerGlobals(currentRenderLayer=layer)
            
            # 배치 렌더링 수행
            cmds.arnoldRender(batch=True)
            print(f"{layer} 레이어의 EXR 렌더링이 완료되었습니다.")
    