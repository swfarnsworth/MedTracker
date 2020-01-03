"""
Updates medications-values.csv, keeping it alphabetized
"""


def main():
    comma_nl = ',\n'
    csv_path = '../alexa_skills_kit/medications-values.csv'

    with open(csv_path) as f:
        text = f.read()

    lines = text.split(comma_nl)
    lines = [line.strip() for line in lines]

    with open('./new_medications.txt') as f:
        text = f.read()

    new_lines = text.split('\n')
    new_lines = [line.strip() for line in new_lines]

    lines += new_lines
    lines.sort()

    output = comma_nl.join(lines) + comma_nl

    with open(csv_path, 'w') as f:
        f.write(output)


if __name__ == '__main__':
    main()