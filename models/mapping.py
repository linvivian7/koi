from user import User
from ratio import ratio_instance
from ratio import Ratio
from model import db
from program import Program


def mapping(user_id=None):

    all_programs = {}
    i = 0

    mapping = {
        "nodes": [],
        "links": []
    }

    if user_id:
        user = User.query.get(user_id)
        outgoing = user.user_outgoing()
        receiving = user.user_receiving()

        for program in receiving:
            if program.receiving_program not in all_programs:
                all_programs[program.receiving_program] = i
                i += 1
                mapping["nodes"].append({"name": program.receiving.program_name,
                                         "group": program.receiving.type_id,
                                         "img": program.receiving.vendor.img})

        for program_from in outgoing:
            if program_from.outgoing_program not in all_programs:
                all_programs[program_from.outgoing_program] = i
                i += 1
                mapping["nodes"].append({"name": program_from.outgoing.program_name,
                                         "group": program_from.outgoing.type_id,
                                         "img": program_from.outgoing.vendor.img})

            for program_to in receiving:
                ratio = ratio_instance(program_from.outgoing_program, program_to.receiving_program)
                if ratio:
                    mapping["links"].append({"source": all_programs[ratio.outgoing_program],
                                             "target": all_programs[ratio.receiving_program],
                                             "value": 1})

    else:
        outgoing = db.session.query(Ratio).distinct(Ratio.outgoing_program).all()
        receiving = db.session.query(Ratio).distinct(Ratio.receiving_program).all()
        ratios = db.session.query(Ratio).join(Program, Program.program_id == Ratio.outgoing_program).all()

        for program in outgoing:
            if program.outgoing_program not in all_programs:
                all_programs[program.outgoing_program] = i
                i += 1
                mapping["nodes"].append({"name": program.outgoing.program_name,
                                         "group": program.outgoing.type_id,
                                         "img": program.outgoing.vendor.img})

        for program in receiving:
            if program.receiving_program not in all_programs:
                all_programs[program.receiving_program] = i
                i += 1
                mapping["nodes"].append({"name": program.receiving.program_name,
                                         "group": program.receiving.type_id,
                                         "img": program.receiving.vendor.img})

        for ratio in ratios:
            mapping["links"].append({"source": all_programs[ratio.outgoing_program],
                                     "target": all_programs[ratio.receiving_program],
                                     "value": 1})

    return mapping
